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
    regeneration_token: str | None
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


def _condense_automation_description(description: str, max_chars: int | None = None) -> str:
    text = str(description or "").strip()
    if not text:
        return "Best-effort local extraction/conversion request."

    primary = text.split("\n\nExecution contract:", 1)[0]
    primary = re.sub(r"[\u00a0\u200b\u200c\u200d\ufeff]", " ", primary)

    segments: list[str] = []
    for raw_line in primary.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        segments.append(line)

    primary = " | ".join(segments).strip()

    if not primary:
        primary = re.sub(r"\s+", " ", text).strip()
    if max_chars is None or len(primary) <= max_chars:
        return primary
    return primary[: max_chars - 3].rstrip() + "..."


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


def _extract_regeneration_token(
    raw_payload: dict[str, Any],
    *,
    metadata: dict[str, Any],
    source_input: dict[str, Any],
) -> str | None:
    raw_values = [
        raw_payload.get("regeneration_token"),
        metadata.get("regeneration_token"),
        source_input.get("regeneration_token"),
    ]
    candidates: list[str] = []
    for raw in raw_values:
        if raw is None:
            continue
        if not isinstance(raw, str) or not raw.strip():
            raise RuntimeError("regeneration_token must be a non-empty string when provided")
        candidates.append(raw.strip())

    if not candidates:
        return None

    distinct = set(candidates)
    if len(distinct) != 1:
        raise RuntimeError(
            "regeneration_token must be consistent across top-level, metadata, and source when repeated"
        )

    token = candidates[0].lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{2,63}", token):
        raise RuntimeError(
            "regeneration_token must match ^[a-z0-9][a-z0-9._:-]{2,63}$"
        )
    return token


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
    metadata = dict(metadata)

    source_input = raw_payload.get("source", {})
    if source_input is None:
        source_input = {}
    if not isinstance(source_input, dict):
        raise RuntimeError("source must be an object when provided")
    source_input = dict(source_input)

    provided_origin_id = raw_payload.get("origin_id") or source_input.get("origin_id")
    if provided_origin_id is not None and not str(provided_origin_id).strip():
        raise RuntimeError("origin_id cannot be blank when provided")
    origin_id = str(provided_origin_id).strip() if provided_origin_id else ""
    if not origin_id:
        origin_id = Path(inbox_filename).stem

    regeneration_token = _extract_regeneration_token(
        raw_payload,
        metadata=metadata,
        source_input=source_input,
    )
    if regeneration_token and not provided_origin_id:
        raise RuntimeError("regeneration_token requires an explicit origin_id")

    request_type = str(raw_payload.get("request_type", "pdf_to_excel_ocr")).strip().lower()
    if request_type != "pdf_to_excel_ocr":
        raise RuntimeError(f"Unsupported request_type: {request_type}")

    inputs = raw_payload.get("input", {})
    if not isinstance(inputs, dict):
        raise RuntimeError("input must be a JSON object")

    payload_hash = _payload_hash(raw_payload)
    dedupe_keys = [f"hash:{payload_hash}"]
    if provided_origin_id:
        if regeneration_token:
            dedupe_keys.insert(0, f"origin_regeneration:{origin_id}:{regeneration_token}")
        else:
            dedupe_keys.insert(0, f"origin:{origin_id}")

    if regeneration_token:
        metadata["regeneration_token"] = regeneration_token
        source_input["regeneration_token"] = regeneration_token

    return {
        "title": title.strip(),
        "description": description.strip(),
        "labels": labels,
        "metadata": metadata,
        "source_input": source_input,
        "origin_id": origin_id,
        "regeneration_token": regeneration_token,
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
    regeneration_token = validated["regeneration_token"]
    title = validated["title"]
    description = validated["description"]
    labels = validated["labels"]
    metadata = validated["metadata"]
    source_input = validated["source_input"]
    automation_description = _condense_automation_description(description)

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
    if regeneration_token:
        source["regeneration_token"] = regeneration_token
    priority = _normalize_priority(raw_payload.get("priority"))

    auto_task = {
        "task_id": _next_task_id(base_dir, "AUTO", origin_id),
        "worker": "automation",
        "task_type": "generate_script",
        "objective": (
            f"{title}. "
            "Generate exactly one runnable local helper script artifact for a best-effort "
            "PDF extraction/conversion attempt using the provided parameters. "
            "Prefer reusing the repository's existing inbox runner and reviewed "
            "PDF-to-Excel implementation when they already satisfy the request "
            "instead of re-implementing the pipeline from scratch."
        ),
        "inputs": {
            "params": {
                "input_dir": input_dir,
                "output_xlsx": output_xlsx,
                "ocr": ocr_mode,
                "dry_run": dry_run,
                "origin_id": origin_id,
                "title": title,
                "description": automation_description,
                "labels": labels,
                "preferred_wrapper_script": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py",
                "preferred_base_script": "artifacts/scripts/pdf_to_excel_ocr.py",
                "reference_docs": [
                    "artifacts/docs/pdf_to_excel_ocr_usage.md",
                    "artifacts/reviews/pdf_to_excel_ocr_review.md",
                ],
                "contract_hints": {
                    "output_format_fidelity": (
                        "If output_xlsx ends with .xlsx, produce a real XLSX workbook "
                        "container or fail honestly before writing mismatched text/XML/CSV "
                        "content to a .xlsx path."
                    ),
                    "path_portability": (
                        "Use the provided input_dir parameter as runtime input. Do not "
                        "hardcode a user-home or absolute input path when params already "
                        "declare the path."
                    ),
                    "traceability": (
                        "Preserve meaningful description context from the external input; "
                        "do not collapse it to a heading fragment such as Purpose:."
                    ),
                    "reuse_preference": (
                        "Prefer reusing artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py as "
                        "the wrapper baseline and artifacts/scripts/pdf_to_excel_ocr.py as the "
                        "reviewed delegate when compatible, so workbook semantics and contract "
                        "behavior stay aligned with repository evidence."
                    ),
                    "outcome_status_model": (
                        "Use the reviewable status model success/partial/failed. Dry-run "
                        "requests or zero-PDF discovery should resolve to partial rather than "
                        "claiming success without an output artifact."
                    ),
                    "delegate_resolution": (
                        "If preferred_base_script is relative, resolve it from the repository "
                        "or script location instead of Path.cwd() so behavior stays portable "
                        "across shells and CI."
                    ),
                    "reviewed_delegate_contract": (
                        "For readonly reviewable preview flows, delegate only to the reviewed "
                        "repository script artifacts/scripts/pdf_to_excel_ocr.py or fail "
                        "honestly instead of broadening behavior through an arbitrary helper."
                    ),
                    "delegate_success_evidence": (
                        "Do not treat zero exit code plus output-file existence as sufficient "
                        "wrapper success evidence on their own. Prefer a structured delegate "
                        "report that confirms a real success outcome with at least one "
                        "processed input and no failed-file counterexamples before the wrapper "
                        "claims success."
                    ),
                    "delegate_timeout": (
                        "Bound delegate subprocess execution with an explicit timeout and "
                        "report timeout as an honest failed/partial outcome instead of "
                        "allowing smoke automation to hang indefinitely."
                    ),
                    "runtime_summary": (
                        "The generated script should emit a structured summary of what it "
                        "produced so later review can inspect behavior without guessing."
                    ),
                    "delegate_report_schema": (
                        "Treat delegate JSON report fields status/total_files/status_counter/"
                        "dry_run as the canonical evidence contract. Do not require undeclared "
                        "processed_files/succeeded_files/failed_files counters."
                    ),
                    "delegate_report_handoff": (
                        "When the delegate prints a JSON report to stdout, parse that JSON "
                        "directly instead of relying only on sidecar-report file path discovery."
                    ),
                    "delegate_report_flag_contract": (
                        "If wrapper passes a sidecar report path to the reviewed delegate, "
                        "use the reviewed delegate CLI flag --report-json (or another "
                        "explicitly supported alias). Do not invent undeclared flags such "
                        "as --report-file."
                    ),
                    "dry_run_semantics": (
                        "If wrapper dry-run short-circuits before delegate execution, keep "
                        "execution.delegated=false and report partial honestly. If wrapper "
                        "does delegate under dry-run, pass through --dry-run explicitly."
                    ),
                    "pdf_discovery_consistency": (
                        "Keep wrapper preflight PDF discovery semantics aligned with the "
                        "reviewed delegate (for example recursive vs non-recursive), so "
                        "wrapper evidence and delegated execution count the same candidate set."
                    ),
                },
            }
        },
        "expected_outputs": [
            {"path": automation_artifact, "type": "script"},
        ],
        "constraints": [
            "Follow the local inbox normalized request",
            "Do not claim unsupported runtime dependencies",
            "Keep output deterministic and executable",
            "Produce only the expected script artifact",
            "Prefer honest, reviewable intermediate behavior over unsupported OCR claims",
            "If the requested output path ends with .xlsx, do not write non-XLSX text/XML/CSV content to that path.",
            "Do not hardcode an input directory when the task params already provide input_dir.",
            "Preserve meaningful traceability from the incoming description instead of collapsing it to a heading fragment.",
            "Prefer wrapping or adapting artifacts/scripts/pdf_to_excel_ocr.py when that existing repo script already matches the requested behavior.",
            "When artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py already exists, prefer updating that reviewed wrapper baseline instead of rewriting a new control flow from scratch.",
            "If dry_run is true or no PDFs are discovered, report a reviewable partial outcome instead of claiming success without an XLSX artifact.",
            "Resolve relative delegate script paths from the repository or script location, not from Path.cwd().",
            "For readonly reviewable preview flows, only delegate to the reviewed repository script artifacts/scripts/pdf_to_excel_ocr.py unless failing honestly.",
            "Do not claim wrapper success from exit code plus output existence alone when the reviewed delegate report does not provide strong enough success evidence.",
            "Use delegate report fields status/total_files/status_counter/dry_run as canonical evidence; do not require undeclared per-counter keys.",
            "When delegate emits JSON to stdout, parse that report directly instead of depending only on sidecar report-file discovery.",
            "When wrapper passes a sidecar report path to the reviewed delegate, use --report-json exactly unless the reviewed delegate explicitly supports another alias.",
            "If wrapper supports dry-run short-circuit semantics, keep execution.delegated=false and preserve partial status honestly.",
            "Keep wrapper PDF discovery semantics aligned with reviewed delegate discovery semantics to avoid preflight/execution evidence drift.",
            "Use an explicit timeout on delegate subprocess execution so the smoke wrapper cannot hang indefinitely.",
        ],
        "priority": priority,
        "source": source,
        "acceptance_criteria": [
            "Produce the expected script artifact at expected_outputs[0].path",
            "Script behavior remains runnable, deterministic, and reviewable",
            "If output_xlsx ends with .xlsx, the artifact must preserve true XLSX output semantics or fail honestly before writing a mismatched format.",
            "Artifact behavior remains parameter-driven for input_dir and output_xlsx rather than hardcoding unrelated local defaults.",
            "Dry-run or zero-input behavior is represented as a reviewable partial outcome instead of artifact-production success.",
            "Relative preferred_base_script resolution remains portable and does not depend on Path.cwd().",
            "Wrapper success requires stronger delegate evidence than zero exit code plus a non-empty output file alone.",
            "Wrapper evidence logic remains compatible with delegate JSON fields status/total_files/status_counter/dry_run.",
            "Delegate report handoff can consume JSON printed to stdout without relying exclusively on report sidecar file discovery.",
            "Wrapper/delegate sidecar report handoff remains CLI-compatible by using --report-json (or another explicitly supported delegate alias).",
            "Dry-run semantics remain explicit: short-circuit stays partial with no delegated execution, or delegated dry-run is passed through honestly.",
            "Wrapper preflight PDF discovery semantics remain aligned with delegate discovery semantics to keep evidence counts consistent.",
            "Delegate execution is bounded by an explicit timeout and reports timeout honestly.",
        ],
        "metadata": {
            "integration_phase": "8B",
            "pipeline": "inbox->adapter->manager->automation->critic",
            "request_type": request_type,
            "payload_hash": payload_hash,
            "regeneration_token": regeneration_token,
            "labels": labels,
            "external_metadata": metadata,
            "automation_contract_profile": "narrow_script_artifact_with_repo_reuse_and_reviewable_runner_contract",
        },
    }

    critic_task = {
        "task_id": _next_task_id(base_dir, "CRITIC", origin_id),
        "worker": "critic",
        "task_type": "review_artifact",
        "objective": (
            "Review the generated inbox runner together with its reviewed delegate "
            "script from the local inbox pipeline and provide a structured verdict "
            "using one of: pass, fail, needs_revision. Always output a review "
            "markdown artifact and include verdict in metadata."
        ),
        "inputs": {
            "artifacts": [
                {"path": automation_artifact, "type": "script"},
                {"path": "artifacts/scripts/pdf_to_excel_ocr.py", "type": "script"},
            ],
            "params": {
                "origin_id": origin_id,
                "title": title,
                "description": description,
                "labels": labels,
                "review_scope": {
                    "primary_artifact": automation_artifact,
                    "paired_artifacts": ["artifacts/scripts/pdf_to_excel_ocr.py"],
                    "goal": (
                        "Audit the wrapper and the reviewed delegate together so the "
                        "review evidence can speak to the end-to-end readonly smoke path."
                    ),
                },
            },
        },
        "expected_outputs": [
            {"path": review_artifact, "type": "review"},
        ],
        "constraints": [
            "Review must be grounded in produced automation artifact",
            "When both wrapper and reviewed delegate snapshots are supplied, evaluate them as one end-to-end readonly pair instead of ignoring the delegate evidence.",
            "Do not invent missing artifact content",
            "Return a clear verdict: pass, fail, or needs_revision",
            "Include metadata.verdict in output",
            "Generate review artifact markdown for expected_outputs[0].path",
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
            "regeneration_token": regeneration_token,
            "labels": labels,
            "external_metadata": metadata,
        },
    }

    return StandardizedInboxTask(
        origin_id=origin_id,
        payload_hash=payload_hash,
        dedupe_keys=dedupe_keys,
        regeneration_token=regeneration_token,
        source=source,
        title=title,
        description=description,
        labels=labels,
        metadata=metadata,
        automation_task=auto_task,
        critic_task=critic_task,
    )
