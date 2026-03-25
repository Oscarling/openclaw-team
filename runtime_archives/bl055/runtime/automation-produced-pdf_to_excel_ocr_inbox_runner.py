#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_INPUT_DIR = "~/Desktop/pdf样本"
DEFAULT_OUTPUT_XLSX = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
DEFAULT_OCR = "auto"
DEFAULT_DRY_RUN = False
DEFAULT_ORIGIN_ID = "trello:69c24cd3c1a2359ddd7a1bf8"
DEFAULT_TITLE = "BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)"
DEFAULT_DESCRIPTION = (
    "Purpose: | Controlled Trello live preview smoke for openclaw-team. | Expected behavior: | "
    "- read-only Trello ingest | - preview creation smoke only | - no business execution claim | "
    "- no Trello writeback expected in this step | Traceability: | - backlog: BL-20260324-014 | "
    "- blocker context: BL-20260324-015 | - created_by: Oscarling | - created_at: 2026-03-24 Asia/Shanghai | "
    "Note: | This card is only for governed smoke verification and should remain open until the smoke is finished."
)
DEFAULT_LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]
DEFAULT_DELEGATE_RELATIVE = "artifacts/scripts/pdf_to_excel_ocr.py"
DEFAULT_TIMEOUT_SECONDS = 600


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_repo_root() -> Path:
    script_path = Path(__file__).resolve()
    parts = script_path.parts
    try:
        idx = parts.index("artifacts")
        return Path(*parts[:idx]) if idx > 0 else Path("/")
    except ValueError:
        return script_path.parent.parent.parent


def expand_user_path(value: str) -> Path:
    return Path(os.path.expanduser(value)).resolve()


def resolve_output_path(value: str, repo_root: Path) -> Path:
    raw = Path(os.path.expanduser(value))
    if raw.is_absolute():
        return raw.resolve()
    return (repo_root / raw).resolve()


def resolve_delegate_path(value: str, repo_root: Path) -> Path:
    raw = Path(value)
    if raw.is_absolute():
        return raw.resolve()
    candidate = (repo_root / raw).resolve()
    return candidate


def discover_pdfs(input_dir: Path) -> List[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(
        [p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"],
        key=lambda p: str(p).lower(),
    )


def parse_json_text(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
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


def status_counter_from(report: Dict[str, Any]) -> Dict[str, int]:
    raw = report.get("status_counter")
    if not isinstance(raw, dict):
        return {}
    result: Dict[str, int] = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            result[str(key)] = int(value)
        elif isinstance(value, int):
            result[str(key)] = value
        else:
            try:
                result[str(key)] = int(value)
            except Exception:
                continue
    return result


def build_base_summary(args: argparse.Namespace, repo_root: Path, input_dir: Path, output_xlsx: Path, delegate_path: Path, pdfs: List[Path]) -> Dict[str, Any]:
    return {
        "status": "partial",
        "title": args.title,
        "origin_id": args.origin_id,
        "mode": "readonly",
        "labels": list(args.labels),
        "description": args.description,
        "request": {
            "input_dir": str(input_dir),
            "output_xlsx": str(output_xlsx),
            "ocr": args.ocr,
            "dry_run": bool(args.dry_run),
        },
        "traceability": {
            "backlog": "BL-20260324-014",
            "blocker_context": "BL-20260324-015",
            "provider": "trello",
            "origin_id": args.origin_id,
        },
        "paths": {
            "repo_root": str(repo_root),
            "delegate_script": str(delegate_path),
        },
        "preflight": {
            "input_dir_exists": input_dir.exists(),
            "input_dir_is_dir": input_dir.is_dir(),
            "pdf_count": len(pdfs),
            "pdf_samples": [str(p) for p in pdfs[:20]],
        },
        "execution": {
            "delegated": False,
            "timeout_seconds": int(args.timeout_seconds),
        },
        "limitations": [],
        "next_steps": [],
        "timestamps": {
            "generated_at": iso_now(),
        },
    }


def finalize(summary: Dict[str, Any]) -> int:
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    status = summary.get("status")
    if status == "success":
        return 0
    if status == "partial":
        return 0
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly reviewable inbox runner for best-effort PDF to Excel conversion.")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-xlsx", default=DEFAULT_OUTPUT_XLSX)
    parser.add_argument("--ocr", default=DEFAULT_OCR)
    parser.add_argument("--dry-run", action="store_true", default=DEFAULT_DRY_RUN)
    parser.add_argument("--origin-id", default=DEFAULT_ORIGIN_ID)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--label", dest="labels", action="append")
    parser.add_argument("--delegate-script", default=DEFAULT_DELEGATE_RELATIVE)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    if not args.labels:
        args.labels = list(DEFAULT_LABELS)

    repo_root = resolve_repo_root()
    input_dir = expand_user_path(args.input_dir)
    output_xlsx = resolve_output_path(args.output_xlsx, repo_root)
    delegate_path = resolve_delegate_path(args.delegate_script, repo_root)
    pdfs = discover_pdfs(input_dir)

    summary = build_base_summary(args, repo_root, input_dir, output_xlsx, delegate_path, pdfs)

    if output_xlsx.suffix.lower() == ".xlsx":
        summary.setdefault("contract", {})["output_format_fidelity"] = "xlsx_required"

    if args.dry_run:
        summary["status"] = "partial"
        summary["limitations"].append("Dry-run requested; wrapper intentionally short-circuited before delegate execution.")
        summary["next_steps"].append("Re-run without --dry-run to attempt reviewed delegate execution and real XLSX generation.")
        return finalize(summary)

    if not input_dir.exists() or not input_dir.is_dir():
        summary["status"] = "partial"
        summary["limitations"].append("Input directory does not exist or is not a directory.")
        summary["next_steps"].append("Provide a valid input directory containing PDF files, then re-run the wrapper.")
        return finalize(summary)

    if len(pdfs) == 0:
        summary["status"] = "partial"
        summary["limitations"].append("No PDF files were discovered during preflight; no XLSX artifact can be honestly claimed.")
        summary["next_steps"].append("Place one or more PDF files under the input directory and re-run the smoke wrapper.")
        return finalize(summary)

    if not delegate_path.exists() or not delegate_path.is_file():
        summary["status"] = "failed"
        summary["limitations"].append("Reviewed delegate script is missing; readonly preview flow will not broaden behavior to an arbitrary helper.")
        summary["next_steps"].append("Restore artifacts/scripts/pdf_to_excel_ocr.py or provide the reviewed delegate at the configured path.")
        return finalize(summary)

    if output_xlsx.suffix.lower() != ".xlsx":
        summary["status"] = "failed"
        summary["limitations"].append("Requested output path does not end with .xlsx; wrapper refuses mismatched workbook semantics.")
        summary["next_steps"].append("Use an .xlsx output path so real workbook container semantics can be honored by the reviewed delegate.")
        return finalize(summary)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_inbox_runner_") as tmpdir:
        report_path = Path(tmpdir) / "delegate_report.json"
        cmd = [
            sys.executable,
            str(delegate_path),
            "--input-dir",
            str(input_dir),
            "--output-xlsx",
            str(output_xlsx),
            "--ocr",
            str(args.ocr),
            "--report-json",
            str(report_path),
        ]

        summary["execution"].update({
            "delegated": True,
            "command": cmd,
            "report_json_path": str(report_path),
            "started_at": iso_now(),
        })

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(1, int(args.timeout_seconds)),
                cwd=str(repo_root),
            )
        except subprocess.TimeoutExpired as exc:
            summary["status"] = "failed"
            summary["execution"].update({
                "timeout": True,
                "returncode": None,
                "finished_at": iso_now(),
            })
            summary["limitations"].append(f"Delegate execution timed out after {int(args.timeout_seconds)} seconds.")
            summary["next_steps"].append("Inspect the reviewed delegate for hangs, reduce input complexity, or increase timeout deliberately after review.")
            stdout_text = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "")
            stderr_text = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", errors="replace") if exc.stderr else "")
            summary["execution"]["stdout_excerpt"] = stdout_text[-4000:]
            summary["execution"]["stderr_excerpt"] = stderr_text[-4000:]
            return finalize(summary)

        stdout_report = parse_json_text(proc.stdout or "")
        sidecar_report = load_json_file(report_path)
        delegate_report = stdout_report if isinstance(stdout_report, dict) else sidecar_report

        summary["execution"].update({
            "timeout": False,
            "returncode": proc.returncode,
            "finished_at": iso_now(),
            "stdout_excerpt": (proc.stdout or "")[-4000:],
            "stderr_excerpt": (proc.stderr or "")[-4000:],
            "delegate_report_source": "stdout" if stdout_report else ("sidecar" if sidecar_report else None),
        })

        if not isinstance(delegate_report, dict):
            summary["status"] = "failed"
            summary["limitations"].append("Delegate did not provide a parseable structured JSON report on stdout or via --report-json sidecar.")
            summary["next_steps"].append("Review the delegate CLI contract and ensure it emits canonical JSON evidence for status/total_files/status_counter/dry_run.")
            return finalize(summary)

        summary["delegate_report"] = delegate_report

        delegate_status = delegate_report.get("status")
        total_files = delegate_report.get("total_files")
        dry_run = delegate_report.get("dry_run")
        counters = status_counter_from(delegate_report)
        failed_count = counters.get("failed", 0)
        partial_count = counters.get("partial", 0)
        excel_written = bool(delegate_report.get("excel_written"))
        output_exists = bool(delegate_report.get("output_exists"))
        output_size_bytes_raw = delegate_report.get("output_size_bytes", 0)
        try:
            output_size_bytes = int(output_size_bytes_raw)
        except Exception:
            output_size_bytes = 0

        success_gates = {
            "status_is_success": delegate_status == "success",
            "total_files_at_least_one": isinstance(total_files, int) and total_files >= 1,
            "dry_run_is_false": dry_run is False,
            "failed_count_zero": failed_count == 0,
            "partial_count_zero": partial_count == 0,
            "excel_written_true": excel_written is True,
            "output_exists_true": output_exists is True,
            "output_size_bytes_positive": output_size_bytes > 0,
        }
        summary["evidence"] = {
            "canonical_fields_used": ["status", "total_files", "status_counter", "dry_run"],
            "success_gates": success_gates,
        }

        if delegate_status == "success" and all(success_gates.values()):
            summary["status"] = "success"
            summary["output"] = {
                "output_xlsx": str(output_xlsx),
                "excel_written": True,
                "output_exists": True,
                "output_size_bytes": output_size_bytes,
            }
            return finalize(summary)

        if delegate_status == "partial":
            summary["status"] = "partial"
            summary["limitations"].append("Reviewed delegate reported a partial outcome; wrapper preserves partial status for best-effort readonly review flow.")
            summary["next_steps"].append("Inspect delegate_report details, remediate partial items, and re-run if stronger evidence is required.")
            if not excel_written or not output_exists or output_size_bytes <= 0:
                summary["limitations"].append("Delegate partial evidence does not attest a completed XLSX write suitable for success promotion.")
            return finalize(summary)

        if delegate_status == "success" and not all(success_gates.values()):
            summary["status"] = "failed"
            summary["limitations"].append("Delegate claimed success but did not satisfy wrapper evidence gates required for honest success attestation.")
            summary["next_steps"].append("Review delegate report fields and ensure workbook output attestation is complete: excel_written=true, output_exists=true, output_size_bytes>0, and no partial/failed counters.")
            return finalize(summary)

        summary["status"] = "failed"
        summary["limitations"].append(f"Delegate returned non-success outcome: {delegate_status!r}.")
        summary["next_steps"].append("Inspect delegate stderr/stdout excerpts and the structured delegate report for remediation details.")
        return finalize(summary)


if __name__ == "__main__":
    sys.exit(main())
