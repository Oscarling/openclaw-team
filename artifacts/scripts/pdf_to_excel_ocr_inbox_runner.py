#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_INPUT_DIR = "~/Desktop/pdf样本"
DEFAULT_OUTPUT_XLSX = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
DEFAULT_OCR = "auto"
DEFAULT_DRY_RUN = False
DEFAULT_ORIGIN_ID = "trello:69c24cd3c1a2359ddd7a1bf8"
DEFAULT_TITLE = "BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)"
DEFAULT_DESCRIPTION = (
    "Purpose: | Controlled Trello live preview smoke for openclaw-team. | "
    "Expected behavior: | - read-only Trello ingest | - preview creation smoke only | "
    "- no business execution cla..."
)
DEFAULT_LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]
DEFAULT_PREFERRED_BASE_SCRIPT = "artifacts/scripts/pdf_to_excel_ocr.py"
DEFAULT_REFERENCE_DOCS = [
    "artifacts/docs/pdf_to_excel_ocr_usage.md",
    "artifacts/reviews/pdf_to_excel_ocr_review.md",
]
RUNNER_PATH = Path(__file__).resolve()
REPO_ROOT = RUNNER_PATH.parents[2]
REVIEWED_BASE_SCRIPT = (REPO_ROOT / DEFAULT_PREFERRED_BASE_SCRIPT).resolve()
ALLOWED_SUMMARY_STATUSES = {"success", "partial", "failed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def expand_path(path_str: str) -> Path:
    return Path(path_str).expanduser()


def resolve_repo_relative_path(path_str: str) -> Path:
    path = expand_path(path_str)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def resolve_delegate_script(path_str: str) -> Path:
    return resolve_repo_relative_path(path_str)


def validate_delegate_script(base_script: Path) -> str | None:
    if base_script != REVIEWED_BASE_SCRIPT:
        return (
            "Preferred base script must resolve to the reviewed repository script "
            f"{REVIEWED_BASE_SCRIPT} to preserve the readonly preview contract."
        )
    return None


def bool_flag(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "on"}:
        return True
    if lowered in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value}")


def discover_pdfs(input_dir: Path) -> list[str]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(str(p) for p in input_dir.rglob("*.pdf") if p.is_file())


def parse_delegate_report(stdout_text: str) -> dict[str, Any] | None:
    stripped = stdout_text.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Best-effort inbox runner that reuses the repository PDF-to-Excel OCR script."
    )
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-xlsx", default=DEFAULT_OUTPUT_XLSX)
    parser.add_argument("--ocr", default=DEFAULT_OCR)
    parser.add_argument("--dry-run", type=bool_flag, default=DEFAULT_DRY_RUN)
    parser.add_argument("--origin-id", default=DEFAULT_ORIGIN_ID)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--labels", nargs="*", default=DEFAULT_LABELS)
    parser.add_argument("--preferred-base-script", default=DEFAULT_PREFERRED_BASE_SCRIPT)
    parser.add_argument("--reference-docs", nargs="*", default=DEFAULT_REFERENCE_DOCS)
    parser.add_argument("--summary-json", default="")
    return parser


def emit_summary(summary: dict[str, Any], summary_json: str) -> None:
    rendered = json.dumps(summary, ensure_ascii=False, indent=2)
    print(rendered)
    if summary_json:
        out_path = expand_path(summary_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()

    input_dir = expand_path(args.input_dir)
    output_xlsx = expand_path(args.output_xlsx)
    base_script = resolve_delegate_script(args.preferred_base_script)
    pdfs = discover_pdfs(input_dir)
    readonly_labels_present = any(str(label).strip().lower() == "readonly" for label in args.labels)
    delegate_contract_error = validate_delegate_script(base_script)

    summary: dict[str, Any] = {
        "status": "failed",
        "runner": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py",
        "requested_at": utc_now(),
        "origin": {
            "origin_id": args.origin_id,
            "title": args.title,
            "description": args.description,
            "labels": args.labels,
        },
        "parameters": {
            "input_dir": str(input_dir),
            "output_xlsx": str(output_xlsx),
            "ocr": args.ocr,
            "dry_run": args.dry_run,
            "preferred_base_script": str(base_script),
            "reference_docs": args.reference_docs,
        },
        "contract": {
            "repo_root": str(REPO_ROOT),
            "reviewed_base_script": str(REVIEWED_BASE_SCRIPT),
            "readonly_labels_present": readonly_labels_present,
            "readonly_delegate_verified": delegate_contract_error is None,
        },
        "discovery": {
            "input_dir_exists": input_dir.exists(),
            "pdf_count": len(pdfs),
            "pdf_samples": pdfs[:10],
        },
        "execution": {
            "delegated": False,
            "command": [],
            "returncode": None,
            "stdout": "",
            "stderr": "",
            "delegate_report": None,
        },
        "output": {
            "exists": False,
            "path": str(output_xlsx),
            "size_bytes": None,
        },
        "notes": [
            "Best-effort wrapper prefers repository reuse over re-implementation.",
            "If XLSX output cannot be produced honestly, the runner reports failure instead of writing mismatched content.",
        ],
    }

    if output_xlsx.suffix.lower() != ".xlsx":
        summary["notes"].append("Requested output path does not end with .xlsx; refusing mismatched workbook contract.")
        emit_summary(summary, args.summary_json)
        return 2

    if delegate_contract_error:
        summary["notes"].append(delegate_contract_error)
        emit_summary(summary, args.summary_json)
        return 5

    if not pdfs:
        summary["status"] = "partial"
        summary["notes"].append("No PDF files were discovered; skipping delegate execution with a reviewable partial outcome.")
        emit_summary(summary, args.summary_json)
        return 0

    if args.dry_run:
        summary["status"] = "partial"
        summary["notes"].append("Dry run requested; no conversion attempted and no XLSX output is claimed.")
        emit_summary(summary, args.summary_json)
        return 0

    if not base_script.exists():
        summary["notes"].append("Preferred base script was not found; no unsupported fallback conversion was attempted.")
        emit_summary(summary, args.summary_json)
        return 3

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(base_script),
        "--input-dir",
        str(input_dir),
        "--output-xlsx",
        str(output_xlsx),
    ]
    if args.ocr:
        cmd.extend(["--ocr", args.ocr])

    summary["execution"]["delegated"] = True
    summary["execution"]["command"] = cmd

    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except Exception as exc:
        summary["execution"]["stderr"] = f"delegate invocation error: {exc}"
        emit_summary(summary, args.summary_json)
        return 4

    summary["execution"]["returncode"] = completed.returncode
    summary["execution"]["stdout"] = completed.stdout
    summary["execution"]["stderr"] = completed.stderr

    delegate_report = parse_delegate_report(completed.stdout)
    summary["execution"]["delegate_report"] = delegate_report

    output_exists = output_xlsx.exists() and output_xlsx.is_file()
    summary["output"]["exists"] = output_exists
    if output_exists:
        summary["output"]["size_bytes"] = output_xlsx.stat().st_size

    delegate_status = ""
    if isinstance(delegate_report, dict):
        candidate = str(delegate_report.get("status", "")).strip().lower()
        if candidate in ALLOWED_SUMMARY_STATUSES:
            delegate_status = candidate

    if completed.returncode == 0 and output_exists:
        if delegate_status == "partial":
            summary["status"] = "partial"
            summary["notes"].append("Delegate reported a reviewable partial outcome; preserving partial status.")
        elif delegate_status == "failed":
            summary["notes"].append("Delegate reported failed status despite producing an XLSX artifact.")
        elif delegate_status == "success":
            summary["status"] = "success"
        else:
            summary["status"] = "partial"
            summary["notes"].append("Delegate produced XLSX output but did not provide a recognized summary status.")
    else:
        if completed.returncode == 0 and not output_exists:
            summary["notes"].append("Delegate exited successfully but expected XLSX output was not found.")
        elif completed.returncode != 0:
            summary["notes"].append("Delegate script returned a non-zero exit code.")

    emit_summary(summary, args.summary_json)
    return 0 if summary["status"] in {"success", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
