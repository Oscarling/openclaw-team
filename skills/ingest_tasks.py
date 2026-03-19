from __future__ import annotations

import argparse
import json
import os
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
PROCESSED_DIR = REPO_ROOT / "processed"
REJECTED_DIR = REPO_ROOT / "rejected"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
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


def normalize_validate(inbox_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    with open(inbox_path, encoding="utf-8") as f:
        raw = json.load(f)

    standardized = normalize_local_inbox_payload(
        raw,
        inbox_filename=inbox_path.name,
        base_dir=REPO_ROOT,
    )
    auto_task = standardized.automation_task
    critic_task = standardized.critic_task

    auto_errors = validate_task(auto_task)
    critic_errors = validate_task(critic_task)
    if auto_errors or critic_errors:
        raise RuntimeError(
            "Task validation failed: "
            + json.dumps(
                {"automation_errors": auto_errors, "critic_errors": critic_errors},
                ensure_ascii=False,
            )
        )
    return auto_task, critic_task


def build_critic_from_automation(critic_task: dict[str, Any], auto_result: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(critic_task))
    artifacts = auto_result.get("artifacts")
    if isinstance(artifacts, list) and artifacts:
        updated.setdefault("inputs", {})
        updated["inputs"]["artifacts"] = artifacts
    return updated


def process_one(inbox_path: Path, test_mode: str) -> dict[str, Any]:
    auto_task: dict[str, Any]
    critic_task: dict[str, Any]
    auto_result: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None

    try:
        auto_task, critic_task = normalize_validate(inbox_path)

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

        moved = move_with_suffix(inbox_path, PROCESSED_DIR)
        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": "processed",
                "automation_task_id": auto_task["task_id"],
                "automation_result": auto_result,
                "critic_task_id": critic_task["task_id"],
                "critic_result": critic_result,
            },
        )
        return {"status": "processed", "file": str(moved), "result_sidecar": str(sidecar)}
    except Exception as exc:
        moved = move_with_suffix(inbox_path, REJECTED_DIR)
        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": "rejected",
                "error": str(exc),
                "automation_result": auto_result,
                "critic_result": critic_result,
            },
        )
        return {"status": "rejected", "file": str(moved), "result_sidecar": str(sidecar), "error": str(exc)}


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

    inbox_files = sorted(INBOX_DIR.glob("*.json"))
    if not inbox_files:
        print(json.dumps({"status": "idle", "message": "No inbox files"}, ensure_ascii=False))
        return 0

    results = []
    for inbox_file in inbox_files:
        result = process_one(inbox_file, args.test_mode)
        results.append(result)

    payload = {
        "status": "done",
        "processed": len([r for r in results if r["status"] == "processed"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "test_mode": args.test_mode,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ARGUS_BASE_DIR", str(REPO_ROOT))
    os.environ.setdefault("ARGUS_APP_HOST_PATH", str(REPO_ROOT))
    raise SystemExit(main())
