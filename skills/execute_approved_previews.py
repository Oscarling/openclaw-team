from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from argus_contracts import validate_task
from skills.delegate_task import delegate_task


PREVIEW_DIR = REPO_ROOT / "preview"
APPROVALS_DIR = REPO_ROOT / "approvals"
VERDICT_VALUES = {"pass", "fail", "needs_revision"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    APPROVALS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute approved preview tasks only; unapproved previews are never dispatched."
    )
    parser.add_argument("--once", action="store_true", help="Process approvals once and exit.")
    parser.add_argument("--preview-id", default=None, help="Run only a specific preview id.")
    parser.add_argument(
        "--test-mode",
        choices=("off", "success", "partial", "failed", "transient_failed"),
        default="success",
        help="Worker test mode routed through delegate_task; use off for real LLM execution.",
    )
    parser.add_argument(
        "--allow-replay",
        action="store_true",
        help="Explicitly allow re-running a preview that has already been executed.",
    )
    return parser.parse_args()


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


def load_approvals(preview_id: str | None) -> list[tuple[Path, dict[str, Any]]]:
    approvals = []
    if preview_id:
        paths = [APPROVALS_DIR / f"{preview_id}.json"]
    else:
        paths = sorted(APPROVALS_DIR.glob("*.json"))
    for path in paths:
        if not path.exists():
            continue
        payload = load_json(path)
        approvals.append((path, payload))
    return approvals


def update_preview_execution(
    *,
    preview_path: Path,
    preview_payload: dict[str, Any],
    decision: str,
    decision_reason: str,
    approval_path: Path,
    approval_payload: dict[str, Any],
    auto_result: dict[str, Any] | None,
    critic_result: dict[str, Any] | None,
    critic_verdict: str,
) -> None:
    execution = preview_payload.get("execution")
    if not isinstance(execution, dict):
        execution = {}
    attempts_raw = execution.get("attempts", 0)
    attempts = int(attempts_raw) if isinstance(attempts_raw, int) or str(attempts_raw).isdigit() else 0
    execution.update(
        {
            "status": decision,
            "executed": True,
            "executed_at": utc_now(),
            "attempts": attempts + 1,
            "decision_reason": decision_reason,
        }
    )
    preview_payload["execution"] = execution
    preview_payload["approved"] = bool(approval_payload.get("approved", False))
    preview_payload["approval"] = {
        "approval_file": str(approval_path),
        "approved_by": approval_payload.get("approved_by"),
        "approved_at": approval_payload.get("approved_at"),
        "note": approval_payload.get("note"),
    }
    preview_payload["last_execution"] = {
        "decision": decision,
        "decision_reason": decision_reason,
        "automation_result": auto_result,
        "critic_result": critic_result,
        "critic_verdict": critic_verdict,
    }
    write_json(preview_path, preview_payload)


def process_approval(approval_path: Path, approval: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    preview_id = str(approval.get("preview_id") or "").strip()
    if not preview_id:
        return {
            "status": "rejected",
            "decision_reason": "approval_missing_preview_id",
            "approval_file": str(approval_path),
        }
    if not bool(approval.get("approved", False)):
        return {
            "status": "skipped",
            "decision_reason": "approval_flag_not_true",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    preview_path = PREVIEW_DIR / f"{preview_id}.json"
    if not preview_path.exists():
        return {
            "status": "rejected",
            "decision_reason": "preview_not_found",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    preview_payload = load_json(preview_path)
    execution = preview_payload.get("execution", {})
    execution_status = str(execution.get("status", "")).strip().lower() if isinstance(execution, dict) else ""
    if execution_status in {"processed", "rejected"} and not args.allow_replay:
        return {
            "status": "skipped",
            "decision_reason": "already_executed_use_allow_replay",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    tasks = preview_payload.get("internal_tasks")
    if not isinstance(tasks, dict):
        return {
            "status": "rejected",
            "decision_reason": "preview_missing_internal_tasks",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    auto_task = tasks.get("automation")
    critic_task = tasks.get("critic")
    auto_errors = validate_task(auto_task)
    critic_errors = validate_task(critic_task)
    if auto_errors or critic_errors:
        return {
            "status": "rejected",
            "decision_reason": "preview_task_validate_failed",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
            "automation_errors": auto_errors,
            "critic_errors": critic_errors,
        }

    auto_result: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None
    verdict = "needs_revision"
    decision = "rejected"
    decision_reason = "execution_failed"

    try:
        dt_kwargs = {
            "timeout": 600,
            "retry_attempts": 0,
        }
        if args.test_mode != "off":
            dt_kwargs["test_mode"] = args.test_mode

        auto_result = delegate_task("automation", auto_task, **dt_kwargs)
        if auto_result.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Automation task failed: {json.dumps(auto_result, ensure_ascii=False)}")

        critic_task = build_critic_from_automation(critic_task, auto_result)
        critic_post_errors = validate_task(critic_task)
        if critic_post_errors:
            raise RuntimeError(
                "Critic task invalid after automation mapping: "
                + json.dumps(critic_post_errors, ensure_ascii=False)
            )

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
    except Exception as exc:
        decision = "rejected"
        decision_reason = str(exc)

    update_preview_execution(
        preview_path=preview_path,
        preview_payload=preview_payload,
        decision=decision,
        decision_reason=decision_reason,
        approval_path=approval_path,
        approval_payload=approval,
        auto_result=auto_result,
        critic_result=critic_result,
        critic_verdict=verdict,
    )

    sidecar = {
        "preview_id": preview_id,
        "approval_file": str(approval_path),
        "executed_at": utc_now(),
        "status": decision,
        "decision_reason": decision_reason,
        "critic_verdict": verdict,
        "test_mode": args.test_mode,
    }
    sidecar_path = APPROVALS_DIR / f"{preview_id}.result.json"
    write_json(sidecar_path, sidecar)

    return {
        "status": decision,
        "decision_reason": decision_reason,
        "preview_id": preview_id,
        "approval_file": str(approval_path),
        "result_sidecar": str(sidecar_path),
        "critic_verdict": verdict,
    }


def main() -> int:
    args = parse_args()
    ensure_dirs()

    approvals = load_approvals(args.preview_id)
    if not approvals:
        print(json.dumps({"status": "idle", "message": "No approval files found."}, ensure_ascii=False))
        return 0

    results = []
    for approval_path, approval in approvals:
        results.append(process_approval(approval_path, approval, args))

    payload = {
        "status": "done",
        "processed": len([r for r in results if r["status"] == "processed"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "skipped": len([r for r in results if r["status"] == "skipped"]),
        "test_mode": args.test_mode,
        "allow_replay": args.allow_replay,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ARGUS_BASE_DIR", str(REPO_ROOT))
    os.environ.setdefault("ARGUS_APP_HOST_PATH", str(REPO_ROOT))
    raise SystemExit(main())
