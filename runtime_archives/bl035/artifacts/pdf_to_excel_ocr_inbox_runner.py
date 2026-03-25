#!/usr/bin/env python3
"""Reviewable inbox wrapper for the reviewed PDF-to-Excel delegate.

This wrapper prefers delegating to the repository-reviewed implementation at
artifacts/scripts/pdf_to_excel_ocr.py and keeps a narrow, evidence-backed
control flow suitable for readonly smoke previews.

Key contract behaviors:
- parameter-driven input/output paths
- portable delegate resolution independent of Path.cwd()
- honest partial outcome for dry-run short-circuit or zero discovered PDFs
- explicit delegate timeout
- canonical evidence from delegate JSON fields:
  status, total_files, status_counter, dry_run
- JSON report handoff via stdout and optional --report-json sidecar
- no claim of success from exit code/output existence alone
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_INPUT_DIR = "~/Desktop/pdf样本"
DEFAULT_OUTPUT_XLSX = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
DEFAULT_OCR = "auto"
DEFAULT_ORIGIN_ID = "trello:69c24cd3c1a2359ddd7a1bf8"
DEFAULT_TITLE = "BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)"
DEFAULT_DESCRIPTION = (
    "Purpose:\n"
    "Controlled Trello live preview smoke for openclaw-team.\n"
    "Expected behavior:\n"
    "- read-only Trello ingest\n"
    "- preview creation smoke only\n"
    "- no business execution claim\n"
    "- no Trello writeback expected in this step\n"
    "Traceability:\n"
    "- backlog: BL-20260324-014\n"
    "- blocker context: BL-20260324-015\n"
    "- created_by: Oscarling\n"
    "- created_at: 2026-03-24 Asia/Shanghai\n"
    "Note:\n"
    "This card is only for governed smoke verification and should remain open until the smoke is finished."
)
DEFAULT_LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_BASE_SCRIPT = "artifacts/scripts/pdf_to_excel_ocr.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): make_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_jsonable(v) for v in value]
    return value


def emit_summary(payload: Dict[str, Any]) -> None:
    print(json.dumps(make_jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Readonly reviewable wrapper around the reviewed PDF-to-Excel OCR delegate."
    )
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR, help="Directory containing PDF inputs.")
    parser.add_argument("--output-xlsx", default=DEFAULT_OUTPUT_XLSX, help="Target XLSX output path.")
    parser.add_argument("--ocr", default=DEFAULT_OCR, help="OCR mode to pass through to the delegate.")
    parser.add_argument("--dry-run", action="store_true", help="Short-circuit reviewable preflight without delegate execution.")
    parser.add_argument("--origin-id", default=DEFAULT_ORIGIN_ID, help="External source origin identifier.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Traceability title.")
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION, help="Traceability description.")
    parser.add_argument("--label", dest="labels", action="append", default=None, help="Repeatable label.")
    parser.add_argument(
        "--base-script",
        default=DEFAULT_BASE_SCRIPT,
        help="Preferred reviewed delegate script path. Relative paths resolve from repo/script location.",
    )
    parser.add_argument(
        "--report-json",
        default=None,
        help="Optional wrapper summary output path. If provided, writes wrapper summary JSON there.",
    )
    parser.add_argument(
        "--delegate-timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Timeout for delegate execution in seconds.",
    )
    return parser.parse_args()


def infer_repo_root(script_path: Path) -> Path:
    # Expected location: <repo>/artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py
    if script_path.parent.name == "scripts" and script_path.parent.parent.name == "artifacts":
        return script_path.parent.parent.parent
    return script_path.parent


def resolve_path(raw_path: str, repo_root: Path, script_dir: Path) -> Path:
    expanded = Path(os.path.expanduser(raw_path))
    if expanded.is_absolute():
        return expanded

    candidate_repo = (repo_root / expanded).resolve()
    if candidate_repo.exists() or raw_path.startswith("artifacts/"):
        return candidate_repo
    return (script_dir / expanded).resolve()


def discover_pdfs(input_dir: Path) -> List[Path]:
    # Recursive discovery to stay aligned with typical delegate processing semantics.
    return sorted(p for p in input_dir.rglob("*.pdf") if p.is_file())


def try_parse_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for idx in range(len(lines)):
        candidate = "\n".join(lines[idx:])
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists() or not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def evaluate_delegate_report(report: Dict[str, Any], output_xlsx: Path) -> Dict[str, Any]:
    status = report.get("status")
    total_files = report.get("total_files")
    status_counter = report.get("status_counter") or {}
    dry_run = bool(report.get("dry_run", False))

    succeeded = int(status_counter.get("success", 0) or 0)
    failed = int(status_counter.get("failed", 0) or 0)
    partial = int(status_counter.get("partial", 0) or 0)

    evidence_ok = (
        status == "success"
        and isinstance(total_files, int)
        and total_files > 0
        and succeeded > 0
        and failed == 0
        and partial == 0
        and not dry_run
        and output_xlsx.exists()
        and output_xlsx.is_file()
        and output_xlsx.stat().st_size > 0
    )

    if evidence_ok:
        wrapper_status = "success"
        rationale = "delegate_report_confirmed_success"
    elif dry_run:
        wrapper_status = "partial"
        rationale = "delegate_report_is_dry_run"
    elif isinstance(total_files, int) and total_files == 0:
        wrapper_status = "partial"
        rationale = "delegate_report_zero_inputs"
    elif status in {"partial", "failed"}:
        wrapper_status = status
        rationale = "delegate_report_non_success"
    else:
        wrapper_status = "partial"
        rationale = "delegate_report_insufficient_success_evidence"

    return {
        "wrapper_status": wrapper_status,
        "rationale": rationale,
        "canonical": {
            "status": status,
            "total_files": total_files,
            "status_counter": status_counter,
            "dry_run": dry_run,
        },
    }


def main() -> int:
    args = parse_args()
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    repo_root = infer_repo_root(script_path)

    input_dir = resolve_path(args.input_dir, repo_root=repo_root, script_dir=script_dir)
    output_xlsx = resolve_path(args.output_xlsx, repo_root=repo_root, script_dir=script_dir)
    delegate_script = resolve_path(args.base_script, repo_root=repo_root, script_dir=script_dir)
    wrapper_report_path = resolve_path(args.report_json, repo_root=repo_root, script_dir=script_dir) if args.report_json else None
    labels = args.labels if args.labels is not None else list(DEFAULT_LABELS)

    summary: Dict[str, Any] = {
        "status": "failed",
        "title": args.title,
        "origin_id": args.origin_id,
        "description": args.description,
        "labels": labels,
        "timestamps": {
            "started_at": utc_now(),
        },
        "request": {
            "input_dir": str(input_dir),
            "output_xlsx": str(output_xlsx),
            "ocr": args.ocr,
            "dry_run": bool(args.dry_run),
        },
        "execution": {
            "wrapper_script": str(script_path),
            "delegated": False,
            "delegate_script": str(delegate_script),
            "delegate_timeout_seconds": int(args.delegate_timeout_seconds),
        },
        "preflight": {},
        "delegate": None,
        "artifacts": {
            "output_xlsx": str(output_xlsx),
            "wrapper_report_json": str(wrapper_report_path) if wrapper_report_path else None,
        },
        "errors": [],
    }

    if output_xlsx.suffix.lower() != ".xlsx":
        summary["status"] = "failed"
        summary["errors"].append("output_xlsx must end with .xlsx to preserve real XLSX semantics")
        summary["timestamps"]["finished_at"] = utc_now()
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 1

    if not delegate_script.exists() or not delegate_script.is_file():
        summary["status"] = "failed"
        summary["errors"].append(f"reviewed delegate not found: {delegate_script}")
        summary["timestamps"]["finished_at"] = utc_now()
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 1

    existing_pdfs = discover_pdfs(input_dir) if input_dir.exists() and input_dir.is_dir() else []
    summary["preflight"] = {
        "input_dir_exists": input_dir.exists(),
        "input_dir_is_dir": input_dir.is_dir(),
        "discovered_pdf_count": len(existing_pdfs),
        "discovered_pdf_samples": [str(p) for p in existing_pdfs[:10]],
    }

    if args.dry_run:
        summary["status"] = "partial"
        summary["timestamps"]["finished_at"] = utc_now()
        summary["notes"] = [
            "Dry-run requested; wrapper intentionally did not delegate.",
            "Reviewable partial outcome with execution.delegated=false.",
        ]
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 0

    if not input_dir.exists() or not input_dir.is_dir():
        summary["status"] = "failed"
        summary["errors"].append(f"input_dir is not a readable directory: {input_dir}")
        summary["timestamps"]["finished_at"] = utc_now()
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 1

    if len(existing_pdfs) == 0:
        summary["status"] = "partial"
        summary["timestamps"]["finished_at"] = utc_now()
        summary["notes"] = [
            "No PDF files discovered during preflight.",
            "Partial outcome reported honestly without claiming XLSX production success.",
        ]
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 0

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)
    delegate_report_path = output_xlsx.with_suffix(output_xlsx.suffix + ".delegate_report.json")

    cmd = [
        sys.executable,
        str(delegate_script),
        "--input-dir",
        str(input_dir),
        "--output-xlsx",
        str(output_xlsx),
        "--ocr",
        str(args.ocr),
        "--report-json",
        str(delegate_report_path),
    ]

    summary["execution"]["delegated"] = True
    summary["execution"]["delegate_command"] = cmd

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=int(args.delegate_timeout_seconds),
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        summary["status"] = "failed"
        summary["delegate"] = {
            "timeout": True,
            "returncode": None,
            "stdout": exc.stdout,
            "stderr": exc.stderr,
            "report_path": str(delegate_report_path),
        }
        summary["errors"].append(f"delegate timed out after {args.delegate_timeout_seconds} seconds")
        summary["timestamps"]["finished_at"] = utc_now()
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 1

    stdout_report = try_parse_json_object(completed.stdout or "")
    sidecar_report = load_json_file(delegate_report_path)
    delegate_report = stdout_report if stdout_report else sidecar_report

    summary["delegate"] = {
        "timeout": False,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "report_path": str(delegate_report_path),
        "report_source": "stdout" if stdout_report else ("sidecar" if sidecar_report else None),
        "report": delegate_report,
    }

    if not isinstance(delegate_report, dict):
        summary["status"] = "partial" if completed.returncode == 0 else "failed"
        summary["errors"].append("delegate did not provide a parseable canonical JSON report via stdout or --report-json sidecar")
        summary["timestamps"]["finished_at"] = utc_now()
        if wrapper_report_path:
            wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        emit_summary(summary)
        return 0 if summary["status"] == "partial" else 1

    evaluation = evaluate_delegate_report(delegate_report, output_xlsx=output_xlsx)
    summary["status"] = evaluation["wrapper_status"]
    summary["delegate"]["evaluation"] = evaluation

    if summary["status"] == "success":
        summary["notes"] = [
            "Wrapper success is backed by canonical delegate report evidence.",
            "Delegate reported successful processing with at least one input and no failed/partial counterexamples.",
        ]
    elif summary["status"] == "partial":
        summary["notes"] = [
            "Wrapper preserved a reviewable partial outcome because canonical success evidence was incomplete.",
            f"Rationale: {evaluation['rationale']}",
        ]
    else:
        summary["errors"].append(f"delegate outcome failed: {evaluation['rationale']}")

    summary["timestamps"]["finished_at"] = utc_now()

    if wrapper_report_path:
        wrapper_report_path.parent.mkdir(parents=True, exist_ok=True)
        wrapper_report_path.write_text(json.dumps(make_jsonable(summary), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    emit_summary(summary)
    return 0 if summary["status"] in {"success", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
