from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class StandardizedInboxTask:
    origin_id: str
    payload_hash: str
    dedupe_keys: list[str]
    source: dict[str, Any]
    title: str
    description: str
    labels: list[str]
    metadata: dict[str, Any]
    automation_task: dict[str, Any]
    critic_task: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_priority(value: Any) -> str:
    value = str(value or "medium").strip().lower()
    if value in {"low", "medium", "high"}:
        return value
    return "medium"


def _payload_hash(raw_payload: dict[str, Any]) -> str:
    text = json.dumps(raw_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_labels(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RuntimeError("labels must be an array of strings when provided")

    pattern = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,31}$")
    labels: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise RuntimeError("labels entries must be strings")
        label = item.strip()
        if not label:
            raise RuntimeError("labels entries must be non-empty strings")
        if not pattern.match(label):
            raise RuntimeError(
                "labels entries must match ^[a-z0-9][a-z0-9_.:-]{0,31}$ "
                f"(invalid: {label})"
            )
        labels.append(label)
    return labels


def validate_external_payload(raw_payload: dict[str, Any], inbox_filename: str) -> dict[str, Any]:
    if not isinstance(raw_payload, dict):
        raise RuntimeError("Inbox payload must be a JSON object")

    title = raw_payload.get("title")
    if not isinstance(title, str) or len(title.strip()) < 3:
        raise RuntimeError("title is required and must be a non-empty string")
    description = raw_payload.get("description")
    if not isinstance(description, str) or len(description.strip()) < 10:
        raise RuntimeError("description is required and must be a non-empty string")

    labels = _validate_labels(raw_payload.get("labels"))
    metadata = raw_payload.get("metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise RuntimeError("metadata must be an object when provided")

    source_input = raw_payload.get("source", {})
    if source_input is None:
        source_input = {}
    if not isinstance(source_input, dict):
        raise RuntimeError("source must be an object when provided")

    provided_origin_id = raw_payload.get("origin_id") or source_input.get("origin_id")
    if provided_origin_id is not None and not str(provided_origin_id).strip():
        raise RuntimeError("origin_id cannot be blank when provided")
    origin_id = str(provided_origin_id).strip() if provided_origin_id else ""
    if not origin_id:
        origin_id = Path(inbox_filename).stem

    request_type = str(raw_payload.get("request_type", "pdf_to_excel_ocr")).strip().lower()
    if request_type != "pdf_to_excel_ocr":
        raise RuntimeError(f"Unsupported request_type: {request_type}")

    inputs = raw_payload.get("input", {})
    if not isinstance(inputs, dict):
        raise RuntimeError("input must be a JSON object")

    payload_hash = _payload_hash(raw_payload)
    dedupe_keys = [f"hash:{payload_hash}"]
    if provided_origin_id:
        dedupe_keys.insert(0, f"origin:{origin_id}")

    return {
        "title": title.strip(),
        "description": description.strip(),
        "labels": labels,
        "metadata": metadata,
        "source_input": source_input,
        "origin_id": origin_id,
        "request_type": request_type,
        "inputs": inputs,
        "payload_hash": payload_hash,
        "dedupe_keys": dedupe_keys,
    }


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
    validated = validate_external_payload(raw_payload, inbox_filename)

    origin_id = validated["origin_id"]
    request_type = validated["request_type"]
    inputs = validated["inputs"]
    payload_hash = validated["payload_hash"]
    dedupe_keys = validated["dedupe_keys"]
    title = validated["title"]
    description = validated["description"]
    labels = validated["labels"]
    metadata = validated["metadata"]
    source_input = validated["source_input"]

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
        "title": title,
        "labels": labels,
    }
    source.update({k: v for k, v in source_input.items() if k not in {"kind"}})
    priority = _normalize_priority(raw_payload.get("priority"))

    auto_task = {
        "task_id": _next_task_id(base_dir, "AUTO", origin_id),
        "worker": "automation",
        "task_type": "generate_script",
        "objective": (
            f"{title}. "
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
                "title": title,
                "description": description,
                "labels": labels,
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
            "integration_phase": "8B",
            "pipeline": "inbox->adapter->manager->automation->critic",
            "request_type": request_type,
            "payload_hash": payload_hash,
            "labels": labels,
            "external_metadata": metadata,
        },
    }

    critic_task = {
        "task_id": _next_task_id(base_dir, "CRITIC", origin_id),
        "worker": "critic",
        "task_type": "review_artifact",
        "objective": (
            "Review automation artifact from local inbox pipeline and provide a "
            "structured verdict using one of: pass, fail, needs_revision."
        ),
        "inputs": {
            "artifacts": [{"path": automation_artifact, "type": "script"}],
            "params": {
                "origin_id": origin_id,
                "title": title,
                "description": description,
                "labels": labels,
            },
        },
        "expected_outputs": [
            {"path": review_artifact, "type": "review"},
        ],
        "constraints": [
            "Review must be grounded in produced automation artifact",
            "Do not invent missing artifact content",
            "Return a clear verdict: pass, fail, or needs_revision",
        ],
        "priority": priority,
        "source": source,
        "acceptance_criteria": [
            "Produce a review artifact with explicit verdict (pass/fail/needs_revision)",
        ],
        "metadata": {
            "integration_phase": "8B",
            "pipeline": "inbox->adapter->manager->automation->critic",
            "request_type": request_type,
            "payload_hash": payload_hash,
            "labels": labels,
            "external_metadata": metadata,
        },
    }

    return StandardizedInboxTask(
        origin_id=origin_id,
        payload_hash=payload_hash,
        dedupe_keys=dedupe_keys,
        source=source,
        title=title,
        description=description,
        labels=labels,
        metadata=metadata,
        automation_task=auto_task,
        critic_task=critic_task,
    )
