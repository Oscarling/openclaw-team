from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.local_inbox_adapter import normalize_local_inbox_payload
from argus_contracts import validate_task
from skills.delegate_task import delegate_task


INBOX_DIR = REPO_ROOT / "inbox"
PROCESSING_DIR = REPO_ROOT / "processing"
PROCESSED_DIR = REPO_ROOT / "processed"
REJECTED_DIR = REPO_ROOT / "rejected"
VERDICT_VALUES = {"pass", "fail", "needs_revision"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)


def move_with_suffix(src: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate = target_dir / src.name
    if not candidate.exists():
        shutil.move(str(src), str(candidate))
        return candidate
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = target_dir / f"{src.stem}.{stamp}{src.suffix}"
    shutil.move(str(src), str(candidate))
    return candidate


def write_result_sidecar(target_file: Path, payload: dict[str, Any]) -> Path:
    sidecar = target_file.with_suffix(target_file.suffix + ".result.json")
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return sidecar


def load_seen_dedupe_keys() -> set[str]:
    seen: set[str] = set()
    for folder in (PROCESSED_DIR, REJECTED_DIR):
        for sidecar in folder.glob("*.result.json"):
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
            except Exception:
                continue
            keys = data.get("dedupe_keys")
            if isinstance(keys, list):
                for key in keys:
                    if isinstance(key, str) and key.strip():
                        seen.add(key.strip())
    return seen


def extract_critic_verdict(critic_result: dict[str, Any], review_artifact_path: str | None) -> str:
    metadata = critic_result.get("metadata")
    if isinstance(metadata, dict):
        verdict = metadata.get("verdict")
        if isinstance(verdict, str):
            norm = verdict.strip().lower()
            if norm in VERDICT_VALUES:
                return norm

    summary = critic_result.get("summary")
    if isinstance(summary, str):
        match = re.search(r"\b(pass|fail|needs_revision)\b", summary.lower())
        if match:
            return match.group(1)

    if review_artifact_path:
        review_path = (REPO_ROOT / review_artifact_path).resolve()
        if review_path.exists():
            text = review_path.read_text(encoding="utf-8", errors="ignore")
            explicit = re.search(r"verdict\s*[:=]\s*(pass|fail|needs_revision)", text, re.I)
            if explicit:
                return explicit.group(1).lower()
            fallback = re.search(r"\b(pass|fail|needs_revision)\b", text.lower())
            if fallback:
                return fallback.group(1)

    status = str(critic_result.get("status", "")).strip().lower()
    if status == "failed":
        return "fail"
    return "needs_revision"


def build_critic_from_automation(critic_task: dict[str, Any], auto_result: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(critic_task))
    artifacts = auto_result.get("artifacts")
    if isinstance(artifacts, list) and artifacts:
        updated.setdefault("inputs", {})
        updated["inputs"]["artifacts"] = artifacts
    return updated


def decision_for_results(auto_result: dict[str, Any], critic_result: dict[str, Any], verdict: str) -> tuple[str, str]:
    auto_status = str(auto_result.get("status", "")).strip().lower()
    critic_status = str(critic_result.get("status", "")).strip().lower()
    if auto_status not in {"success", "partial"}:
        return "rejected", f"automation_status={auto_status}"
    if critic_status not in {"success", "partial"}:
        return "rejected", f"critic_status={critic_status}"
    if verdict == "pass":
        return "processed", "critic_verdict=pass"
    return "rejected", f"critic_verdict={verdict}"


def process_one(processing_file: Path, test_mode: str, seen_dedupe_keys: set[str]) -> dict[str, Any]:
    auto_task: dict[str, Any]
    critic_task: dict[str, Any]
    auto_result: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None
    standardized = None
    raw_payload: dict[str, Any] | None = None
    verdict = "needs_revision"
    decision_reason = "unknown"

    try:
        with open(processing_file, encoding="utf-8") as f:
            raw_payload = json.load(f)

        standardized = normalize_local_inbox_payload(
            raw_payload,
            inbox_filename=processing_file.name,
            base_dir=REPO_ROOT,
        )

        duplicate_keys = [key for key in standardized.dedupe_keys if key in seen_dedupe_keys]
        if duplicate_keys:
            raise RuntimeError(
                "duplicate inbox input detected; keys="
                + ",".join(duplicate_keys)
            )

        auto_task = standardized.automation_task
        critic_task = standardized.critic_task

        auto_errors = validate_task(auto_task)
        critic_errors = validate_task(critic_task)
        if auto_errors or critic_errors:
            raise RuntimeError(
                "task_validate_failed "
                + json.dumps(
                    {"automation_errors": auto_errors, "critic_errors": critic_errors},
                    ensure_ascii=False,
                )
            )

        dt_kwargs = {
            "timeout": 600,
            "retry_attempts": 0,
        }
        if test_mode != "off":
            dt_kwargs["test_mode"] = test_mode

        auto_result = delegate_task("automation", auto_task, **dt_kwargs)
        if auto_result.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Automation task failed: {json.dumps(auto_result, ensure_ascii=False)}")

        critic_task = build_critic_from_automation(critic_task, auto_result)
        critic_errors = validate_task(critic_task)
        if critic_errors:
            raise RuntimeError(f"Critic task invalid after mapping: {critic_errors}")

        critic_result = delegate_task("critic", critic_task, **dt_kwargs)
        if critic_result.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Critic task failed: {json.dumps(critic_result, ensure_ascii=False)}")

        review_artifact_path = None
        artifacts = critic_result.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            first = artifacts[0]
            if isinstance(first, dict):
                review_artifact_path = first.get("path")
            elif isinstance(first, str):
                review_artifact_path = first

        verdict = extract_critic_verdict(critic_result, review_artifact_path)
        decision, decision_reason = decision_for_results(auto_result, critic_result, verdict)
        target_dir = PROCESSED_DIR if decision == "processed" else REJECTED_DIR
        moved = move_with_suffix(processing_file, target_dir)

        if standardized:
            for key in standardized.dedupe_keys:
                seen_dedupe_keys.add(key)

        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": decision,
                "decision": decision,
                "decision_reason": decision_reason,
                "origin_id": None if standardized is None else standardized.origin_id,
                "payload_hash": None if standardized is None else standardized.payload_hash,
                "dedupe_keys": [] if standardized is None else standardized.dedupe_keys,
                "title": None if standardized is None else standardized.title,
                "labels": [] if standardized is None else standardized.labels,
                "automation_task_id": auto_task["task_id"],
                "automation_result": auto_result,
                "critic_task_id": critic_task["task_id"],
                "critic_result": critic_result,
                "critic_verdict": verdict,
            },
        )
        return {
            "status": decision,
            "decision_reason": decision_reason,
            "file": str(moved),
            "result_sidecar": str(sidecar),
            "critic_verdict": verdict,
        }
    except Exception as exc:
        moved = move_with_suffix(processing_file, REJECTED_DIR)
        decision = "rejected"
        reason_text = str(exc)
        if "duplicate inbox input detected" in reason_text:
            decision = "duplicate_skipped"
        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": "rejected",
                "decision": decision,
                "decision_reason": reason_text,
                "error": reason_text,
                "origin_id": None if standardized is None else standardized.origin_id,
                "payload_hash": None if standardized is None else standardized.payload_hash,
                "dedupe_keys": [] if standardized is None else standardized.dedupe_keys,
                "title": None if standardized is None else standardized.title,
                "automation_result": auto_result,
                "critic_result": critic_result,
                "critic_verdict": verdict,
            },
        )
        if standardized:
            for key in standardized.dedupe_keys:
                seen_dedupe_keys.add(key)
        return {
            "status": "rejected",
            "decision": decision,
            "decision_reason": reason_text,
            "file": str(moved),
            "result_sidecar": str(sidecar),
            "error": reason_text,
        }


def claim_inbox_file(inbox_file: Path) -> Path:
    return move_with_suffix(inbox_file, PROCESSING_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest local inbox JSON and dispatch via Manager pipeline.")
    parser.add_argument("--once", action="store_true", help="Process current inbox files once and exit.")
    parser.add_argument(
        "--test-mode",
        choices=("off", "success", "partial", "failed", "transient_failed"),
        default="success",
        help="Worker test mode routed through delegate_task; use off for real LLM execution.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    recovered_processing_files = sorted(PROCESSING_DIR.glob("*.json"))
    inbox_files = sorted(INBOX_DIR.glob("*.json"))
    if not recovered_processing_files and not inbox_files:
        print(json.dumps({"status": "idle", "message": "No inbox files"}, ensure_ascii=False))
        return 0

    claimed_files: list[Path] = []
    for inbox_file in inbox_files:
        claimed_files.append(claim_inbox_file(inbox_file))

    processing_files = recovered_processing_files + claimed_files
    seen_dedupe_keys = load_seen_dedupe_keys()

    results = []
    for processing_file in processing_files:
        result = process_one(processing_file, args.test_mode, seen_dedupe_keys)
        results.append(result)

    payload = {
        "status": "done",
        "processed": len([r for r in results if r["status"] == "processed"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "duplicate_skipped": len([r for r in results if r.get("decision") == "duplicate_skipped"]),
        "inbox_claimed": len(claimed_files),
        "processing_recovered": len(recovered_processing_files),
        "test_mode": args.test_mode,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ARGUS_BASE_DIR", str(REPO_ROOT))
    os.environ.setdefault("ARGUS_APP_HOST_PATH", str(REPO_ROOT))
    raise SystemExit(main())
