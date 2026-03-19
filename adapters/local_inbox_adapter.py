from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StandardizedInboxTask:
    origin_id: str
    source: dict[str, Any]
    automation_task: dict[str, Any]
    critic_task: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_priority(value: Any) -> str:
    value = str(value or "medium").strip().lower()
    if value in {"low", "medium", "high"}:
        return value
    return "medium"


def _next_task_id(base_dir: Path, prefix: str, origin_id: str) -> str:
    date_text = datetime.now(timezone.utc).strftime("%Y%m%d")
    task_dir = base_dir / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)

    seed = int(hashlib.sha1(f"{prefix}:{origin_id}".encode("utf-8")).hexdigest(), 16)
    candidate = (seed % 900) + 100

    for _ in range(1000):
        task_id = f"{prefix}-{date_text}-{candidate:03d}"
        if not (task_dir / f"{task_id}.json").exists():
            return task_id
        candidate = 100 if candidate >= 999 else candidate + 1
    raise RuntimeError(f"Unable to allocate task id for prefix {prefix}")


def normalize_local_inbox_payload(
    raw_payload: dict[str, Any],
    *,
    inbox_filename: str,
    base_dir: Path,
) -> StandardizedInboxTask:
    if not isinstance(raw_payload, dict):
        raise RuntimeError("Inbox payload must be a JSON object")

    origin_id = str(raw_payload.get("origin_id") or Path(inbox_filename).stem).strip()
    if not origin_id:
        raise RuntimeError("origin_id is required")

    request_type = str(raw_payload.get("request_type", "pdf_to_excel_ocr")).strip().lower()
    if request_type != "pdf_to_excel_ocr":
        raise RuntimeError(f"Unsupported request_type: {request_type}")

    inputs = raw_payload.get("input", {})
    if not isinstance(inputs, dict):
        raise RuntimeError("input must be a JSON object")

    input_dir = str(inputs.get("input_dir", "~/Desktop/pdf样本")).strip()
    output_xlsx = str(
        inputs.get("output_xlsx", "artifacts/outputs/phase8a/pdf_to_excel_from_inbox.xlsx")
    ).strip()
    ocr_mode = str(inputs.get("ocr", "auto")).strip().lower()
    dry_run = bool(inputs.get("dry_run", False))

    automation_artifact = "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py"
    review_artifact = "artifacts/reviews/pdf_to_excel_ocr_inbox_review.md"

    source = {
        "kind": "local_inbox",
        "origin_id": origin_id,
        "inbox_file": inbox_filename,
        "received_at": _utc_now(),
    }
    priority = _normalize_priority(raw_payload.get("priority"))

    auto_task = {
        "task_id": _next_task_id(base_dir, "AUTO", origin_id),
        "worker": "automation",
        "task_type": "generate_script",
        "objective": (
            "Generate a runnable helper script for PDF to Excel OCR batch workflow "
            "based on local inbox request parameters."
        ),
        "inputs": {
            "params": {
                "input_dir": input_dir,
                "output_xlsx": output_xlsx,
                "ocr": ocr_mode,
                "dry_run": dry_run,
                "origin_id": origin_id,
            }
        },
        "expected_outputs": [
            {"path": automation_artifact, "type": "script"},
        ],
        "constraints": [
            "Follow the local inbox normalized request",
            "Do not claim unsupported runtime dependencies",
            "Keep output deterministic and executable",
        ],
        "priority": priority,
        "source": source,
        "acceptance_criteria": [
            "Produce at least one script artifact",
            "Script purpose aligns with PDF to Excel OCR scenario",
        ],
        "metadata": {
            "integration_phase": "8A",
            "pipeline": "inbox->adapter->manager->automation->critic",
            "request_type": request_type,
        },
    }

    critic_task = {
        "task_id": _next_task_id(base_dir, "CRITIC", origin_id),
        "worker": "critic",
        "task_type": "review_artifact",
        "objective": (
            "Review automation artifact from local inbox pipeline and provide a "
            "structured quality verdict."
        ),
        "inputs": {
            "artifacts": [{"path": automation_artifact, "type": "script"}],
            "params": {"origin_id": origin_id},
        },
        "expected_outputs": [
            {"path": review_artifact, "type": "review"},
        ],
        "constraints": [
            "Review must be grounded in produced automation artifact",
            "Do not invent missing artifact content",
        ],
        "priority": priority,
        "source": source,
        "acceptance_criteria": [
            "Produce a review artifact with pass/fail style conclusion",
        ],
        "metadata": {
            "integration_phase": "8A",
            "pipeline": "inbox->adapter->manager->automation->critic",
            "request_type": request_type,
        },
    }

    return StandardizedInboxTask(
        origin_id=origin_id,
        source=source,
        automation_task=auto_task,
        critic_task=critic_task,
    )
