from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_WORKERS = ("architect", "devops", "automation", "critic")
WORKER_TASK_TYPES = {
    "architect": "design_architecture",
    "devops": "setup_infrastructure",
    "automation": "generate_script",
    "critic": "review_artifact",
}
ALLOWED_TASK_TYPES = tuple(WORKER_TASK_TYPES.values())
ALLOWED_ARTIFACT_TYPES = ("architecture", "script", "config", "review", "doc")

TASK_TOP_LEVEL_KEYS = {
    "task_id",
    "worker",
    "task_type",
    "objective",
    "inputs",
    "expected_outputs",
    "constraints",
    "priority",
    "source",
    "acceptance_criteria",
    "metadata",
}
OUTPUT_TOP_LEVEL_KEYS = {
    "task_id",
    "worker",
    "status",
    "summary",
    "artifacts",
    "errors",
    "notes",
    "metadata",
    "duration_ms",
    "timestamp",
}
SOURCE_KINDS = {"simulated_trello", "trello", "manual", "internal"}
TASK_ID_PATTERNS = {
    "architect": re.compile(r"^ARCH-[0-9]{8}-[0-9]{3}$"),
    "devops": re.compile(r"^DEVOPS-[0-9]{8}-[0-9]{3}$"),
    "automation": re.compile(r"^AUTO-[0-9]{8}-[0-9]{3}$"),
    "critic": re.compile(r"^CRITIC-[0-9]{8}-[0-9]{3}$"),
}
TASK_ID_RE = re.compile(r"^(ARCH|DEVOPS|AUTO|CRITIC)-[0-9]{8}-[0-9]{3}$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def duration_ms(start_ts: float, end_ts: float) -> float:
    return round(max(0.0, end_ts - start_ts) * 1000, 3)


def resolve_base_dir(base_dir: str | Path | None = None) -> Path:
    raw = base_dir or os.environ.get("ARGUS_BASE_DIR") or "/app"
    return Path(raw).resolve()


def is_relative_artifact_path(path: Any) -> bool:
    return isinstance(path, str) and path.startswith("artifacts/")


def _is_non_empty_string(value: Any, min_length: int = 1) -> bool:
    return isinstance(value, str) and len(value.strip()) >= min_length


def _clean_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if _is_non_empty_string(item):
            items.append(item.strip())
    return items


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def ensure_artifact_path(base_dir: str | Path | None, relative_path: str) -> Path:
    if not is_relative_artifact_path(relative_path):
        raise ValueError(f"Artifact path must start with artifacts/: {relative_path!r}")
    root = resolve_base_dir(base_dir)
    artifact_root = (root / "artifacts").resolve()
    target = (root / relative_path).resolve()
    if not _is_within(target, artifact_root):
        raise ValueError(f"Artifact path escapes artifacts/: {relative_path!r}")
    return target


def validate_artifact(artifact: Any, field_name: str = "artifact") -> list[str]:
    errors: list[str] = []
    if not isinstance(artifact, dict):
        return [f"{field_name} must be an object."]

    unknown = sorted(set(artifact) - {"path", "type"})
    if unknown:
        errors.append(f"{field_name} has unsupported fields: {', '.join(unknown)}")

    if not is_relative_artifact_path(artifact.get("path")):
        errors.append(f"{field_name}.path must start with artifacts/.")

    if artifact.get("type") not in ALLOWED_ARTIFACT_TYPES:
        errors.append(
            f"{field_name}.type must be one of: {', '.join(ALLOWED_ARTIFACT_TYPES)}."
        )
    return errors


def validate_task(task: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(task, dict):
        return ["Task contract must be a JSON object."]

    unknown = sorted(set(task) - TASK_TOP_LEVEL_KEYS)
    if unknown:
        errors.append(f"Task has unsupported top-level fields: {', '.join(unknown)}")

    required = [
        "task_id",
        "worker",
        "task_type",
        "objective",
        "inputs",
        "expected_outputs",
        "constraints",
    ]
    for key in required:
        if key not in task:
            errors.append(f"Task missing required field: {key}")

    task_id = task.get("task_id")
    if not _is_non_empty_string(task_id):
        errors.append("task_id must be a non-empty string.")
    elif not TASK_ID_RE.match(task_id):
        errors.append("task_id must match ^(ARCH|DEVOPS|AUTO|CRITIC)-YYYYMMDD-NNN$.")

    worker = task.get("worker")
    if worker not in ALLOWED_WORKERS:
        errors.append(f"worker must be one of: {', '.join(ALLOWED_WORKERS)}.")

    task_type = task.get("task_type")
    if task_type not in ALLOWED_TASK_TYPES:
        errors.append(f"task_type must be one of: {', '.join(ALLOWED_TASK_TYPES)}.")

    if worker in WORKER_TASK_TYPES:
        expected_task_type = WORKER_TASK_TYPES[worker]
        if task_type != expected_task_type:
            errors.append(
                f"task_type for worker {worker} must be {expected_task_type}, got {task_type!r}."
            )
        pattern = TASK_ID_PATTERNS[worker]
        if _is_non_empty_string(task_id) and not pattern.match(task_id):
            errors.append(f"task_id does not match worker prefix for {worker}: {task_id}")

    if not _is_non_empty_string(task.get("objective"), min_length=10):
        errors.append("objective must be a string with at least 10 characters.")

    if not isinstance(task.get("inputs"), dict):
        errors.append("inputs must be an object.")

    expected_outputs = task.get("expected_outputs")
    if not isinstance(expected_outputs, list) or not expected_outputs:
        errors.append("expected_outputs must be a non-empty array.")
    else:
        for index, artifact in enumerate(expected_outputs):
            errors.extend(validate_artifact(artifact, f"expected_outputs[{index}]"))

    constraints = task.get("constraints")
    if not isinstance(constraints, list):
        errors.append("constraints must be an array.")
    else:
        for index, item in enumerate(constraints):
            if not _is_non_empty_string(item):
                errors.append(f"constraints[{index}] must be a non-empty string.")

    acceptance = task.get("acceptance_criteria")
    if acceptance is not None:
        if not isinstance(acceptance, list):
            errors.append("acceptance_criteria must be an array when provided.")
        else:
            for index, item in enumerate(acceptance):
                if not _is_non_empty_string(item):
                    errors.append(f"acceptance_criteria[{index}] must be a non-empty string.")

    source = task.get("source")
    if source is not None:
        if not isinstance(source, dict):
            errors.append("source must be an object when provided.")
        else:
            kind = source.get("kind")
            if kind is not None and kind not in SOURCE_KINDS:
                errors.append(f"source.kind must be one of: {', '.join(sorted(SOURCE_KINDS))}.")

    metadata = task.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata must be an object when provided.")

    return errors


def validate_output(output: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(output, dict):
        return ["Output contract must be a JSON object."]

    unknown = sorted(set(output) - OUTPUT_TOP_LEVEL_KEYS)
    if unknown:
        errors.append(f"Output has unsupported top-level fields: {', '.join(unknown)}")

    required = ["task_id", "worker", "status", "summary", "artifacts", "timestamp"]
    for key in required:
        if key not in output:
            errors.append(f"Output missing required field: {key}")

    task_id = output.get("task_id")
    if not _is_non_empty_string(task_id):
        errors.append("output.task_id must be a non-empty string.")
    elif not TASK_ID_RE.match(task_id):
        errors.append("output.task_id must match ^(ARCH|DEVOPS|AUTO|CRITIC)-YYYYMMDD-NNN$.")

    worker = output.get("worker")
    if worker not in ALLOWED_WORKERS:
        errors.append(f"output.worker must be one of: {', '.join(ALLOWED_WORKERS)}.")
    elif _is_non_empty_string(task_id) and not TASK_ID_PATTERNS[worker].match(task_id):
        errors.append(f"output.task_id does not match worker prefix for {worker}: {task_id}")

    status = output.get("status")
    if status not in {"success", "failed", "partial"}:
        errors.append("output.status must be one of: success, failed, partial.")

    if not _is_non_empty_string(output.get("summary")):
        errors.append("output.summary must be a non-empty string.")

    artifacts = output.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("output.artifacts must be an array.")
        artifacts = []
    else:
        for index, artifact in enumerate(artifacts):
            errors.extend(validate_artifact(artifact, f"artifacts[{index}]"))

    if status in {"success", "partial"} and len(artifacts) < 1:
        errors.append(f"output.status={status} requires at least one artifact.")

    errors_field = output.get("errors")
    if errors_field is not None:
        if not isinstance(errors_field, list):
            errors.append("output.errors must be an array when provided.")
        else:
            for index, item in enumerate(errors_field):
                if not _is_non_empty_string(item):
                    errors.append(f"output.errors[{index}] must be a non-empty string.")

    notes_field = output.get("notes")
    if notes_field is not None:
        if not isinstance(notes_field, list):
            errors.append("output.notes must be an array when provided.")
        else:
            for index, item in enumerate(notes_field):
                if not _is_non_empty_string(item):
                    errors.append(f"output.notes[{index}] must be a non-empty string.")

    metadata = output.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("output.metadata must be an object when provided.")

    duration = output.get("duration_ms")
    if duration is not None and not isinstance(duration, (int, float)):
        errors.append("output.duration_ms must be a number when provided.")
    elif isinstance(duration, (int, float)) and duration < 0:
        errors.append("output.duration_ms must be >= 0.")

    if not _is_non_empty_string(output.get("timestamp")):
        errors.append("output.timestamp must be a non-empty ISO-8601 string.")

    return errors


def normalize_task_status(output_status: Any) -> str:
    if output_status == "success":
        return "success"
    if output_status == "partial":
        return "partial"
    return "failed"


def build_failure_output(
    task: dict[str, Any],
    errors: list[str] | tuple[str, ...] | None,
    *,
    summary: str | None = None,
    notes: list[str] | tuple[str, ...] | None = None,
    duration_ms_value: float | int | None = None,
) -> dict[str, Any]:
    clean_errors = _clean_string_list(list(errors or []))
    clean_notes = _clean_string_list(list(notes or []))
    output: dict[str, Any] = {
        "task_id": task.get("task_id", "ARCH-19700101-000"),
        "worker": task.get("worker", "architect"),
        "status": "failed",
        "summary": summary or "Task failed.",
        "artifacts": [],
        "timestamp": utc_now_iso(),
    }
    if clean_errors:
        output["errors"] = clean_errors
    if clean_notes:
        output["notes"] = clean_notes
    if duration_ms_value is not None:
        output["duration_ms"] = float(duration_ms_value)

    validation_errors = validate_output(output)
    if validation_errors:
        raise ValueError("Invalid synthesized failure output: " + "; ".join(validation_errors))
    return output
