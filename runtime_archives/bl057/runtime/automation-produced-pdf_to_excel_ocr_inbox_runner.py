#!/usr/bin/env python3
"""Reviewable inbox-style wrapper for the reviewed PDF-to-Excel OCR delegate.

This helper prefers repository reuse over reimplementation. It performs:
- portable delegate resolution relative to repository/script location
- honest preflight PDF discovery aligned to recursive semantics
- dry-run short-circuit as partial without delegate execution
- bounded delegate execution with explicit timeout
- delegate JSON report handoff via stdout and --report-json sidecar
- success gating based on structured evidence, not only exit code/output existence

It is intentionally best-effort and reviewable for readonly smoke usage.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_INPUT_DIR = "~/Desktop/pdf样本"
DEFAULT_OUTPUT_XLSX = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
DEFAULT_OCR = "auto"
DEFAULT_TIMEOUT_SECONDS = 300
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
DEFAULT_PREFERRED_BASE = "artifacts/scripts/pdf_to_excel_ocr.py"


def _expand(path_text: str) -> Path:
    return Path(os.path.expanduser(path_text)).resolve()


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "artifacts").exists():
            return candidate
    return here.parent.parent.parent


def _resolve_delegate(preferred: str) -> Path:
    candidate = Path(preferred)
    if candidate.is_absolute():
        return candidate
    root = _repo_root()
    from_script_dir = (Path(__file__).resolve().parent / candidate).resolve()
    from_root = (root / candidate).resolve()
    if from_root.exists():
        return from_root
    return from_script_dir


def _discover_pdfs(input_dir: Path) -> List[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(
        [
            p for p in input_dir.rglob("*")
            if p.is_file() and p.suffix.lower() == ".pdf"
        ],
        key=lambda p: str(p).lower(),
    )


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return None
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        for end in range(len(text), start, -1):
            chunk = text[start:end].strip()
            if not chunk.endswith("}"):
                continue
            try:
                value = json.loads(chunk)
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
        start = text.find("{", start + 1)
    return None


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        return None
    return None


def _output_attestation(path: Path) -> Dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else 0
    return {
        "excel_written": bool(exists and path.suffix.lower() == ".xlsx" and size > 0),
        "output_exists": bool(exists),
        "output_size_bytes": int(size),
        "output_path": str(path),
    }


def _normalize_counter(value: Any) -> Dict[str, int]:
    if not isinstance(value, dict):
        return {"success": 0, "partial": 0, "failed": 0}
    return {
        "success": int(value.get("success", 0) or 0),
        "partial": int(value.get("partial", 0) or 0),
        "failed": int(value.get("failed", 0) or 0),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reviewable PDF-to-Excel OCR inbox runner")
    parser.add_argument("--input-dir", default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-xlsx", default=DEFAULT_OUTPUT_XLSX)
    parser.add_argument("--ocr", default=DEFAULT_OCR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--origin-id", default=DEFAULT_ORIGIN_ID)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--label", action="append", dest="labels")
    parser.add_argument("--preferred-base-script", default=DEFAULT_PREFERRED_BASE)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    labels = args.labels if args.labels else list(DEFAULT_LABELS)
    input_dir = _expand(args.input_dir)
    output_xlsx = _expand(args.output_xlsx)
    delegate_path = _resolve_delegate(args.preferred_base_script)
    discovered_pdfs = _discover_pdfs(input_dir)

    result: Dict[str, Any] = {
        "status": "failed",
        "summary": "",
        "request": {
            "origin_id": args.origin_id,
            "title": args.title,
            "description": args.description,
            "labels": labels,
            "ocr": args.ocr,
            "dry_run": bool(args.dry_run),
            "input_dir": str(input_dir),
            "output_xlsx": str(output_xlsx),
        },
        "preflight": {
            "delegate_path": str(delegate_path),
            "delegate_exists": delegate_path.exists(),
            "input_dir_exists": input_dir.exists(),
            "input_dir_is_dir": input_dir.is_dir(),
            "pdf_discovery_mode": "recursive",
            "discovered_pdf_count": len(discovered_pdfs),
            "discovered_pdfs": [str(p) for p in discovered_pdfs],
        },
        "execution": {
            "delegated": False,
            "timeout_seconds": int(args.timeout_seconds),
        },
        "delegate": None,
        "output_attestation": _output_attestation(output_xlsx),
        "limitations": [],
        "next_steps": [],
    }

    if output_xlsx.suffix.lower() != ".xlsx":
        result["status"] = "failed"
        result["summary"] = "Requested output path does not end with .xlsx; refusing mismatched output semantics."
        result["limitations"].append("Output path must end with .xlsx for workbook semantics.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if not delegate_path.exists():
        result["status"] = "failed"
        result["summary"] = "Reviewed delegate script was not found; wrapper refuses to broaden behavior."
        result["limitations"].append("Delegate missing: only reviewed repository delegate is allowed for readonly preview flows.")
        result["next_steps"].append("Restore or provide artifacts/scripts/pdf_to_excel_ocr.py at the expected repository location.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if args.dry_run:
        result["status"] = "partial"
        result["summary"] = "Dry-run requested; wrapper performed preflight only and did not delegate execution."
        result["limitations"].append("No XLSX artifact is produced during wrapper short-circuit dry-run.")
        result["next_steps"].append("Run without --dry-run to attempt reviewed delegate conversion.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if len(discovered_pdfs) == 0:
        result["status"] = "partial"
        result["summary"] = "No PDF files were discovered under the provided input directory."
        result["limitations"].append("No candidate PDFs found for conversion, so no XLSX was produced.")
        result["next_steps"].append("Place one or more PDF files in the input directory and rerun the helper.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_delegate_") as tmp_dir:
        report_json = Path(tmp_dir) / "delegate_report.json"
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
            str(report_json),
        ]

        result["execution"]["delegated"] = True
        result["execution"]["command"] = cmd

        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(1, int(args.timeout_seconds)),
                check=False,
            )
            stdout_json = _extract_json_object(completed.stdout or "")
            sidecar_json = _load_json_file(report_json)
            delegate_report = stdout_json or sidecar_json or {}
            result["delegate"] = {
                "returncode": int(completed.returncode),
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "report_source": (
                    "stdout_json" if stdout_json is not None else
                    "sidecar_json" if sidecar_json is not None else
                    "none"
                ),
                "report": delegate_report,
            }
        except subprocess.TimeoutExpired as exc:
            result["status"] = "failed"
            result["summary"] = f"Delegate execution timed out after {int(args.timeout_seconds)} seconds."
            result["delegate"] = {
                "timeout": True,
                "stdout": exc.stdout,
                "stderr": exc.stderr,
                "report_source": "none",
                "report": {},
            }
            result["limitations"].append("Delegate subprocess did not complete within the explicit timeout.")
            result["next_steps"].append("Retry with a larger --timeout-seconds value or reduce the input set.")
            result["output_attestation"] = _output_attestation(output_xlsx)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1

    report = result["delegate"].get("report") if isinstance(result.get("delegate"), dict) else {}
    if not isinstance(report, dict):
        report = {}

    delegate_status = report.get("status")
    delegate_total_files = int(report.get("total_files", 0) or 0)
    delegate_dry_run = bool(report.get("dry_run", False))
    status_counter = _normalize_counter(report.get("status_counter"))

    attestation = _output_attestation(output_xlsx)
    report_excel_written = report.get("excel_written")
    report_output_exists = report.get("output_exists")
    report_output_size_bytes = report.get("output_size_bytes")
    if isinstance(report_excel_written, bool):
        attestation["excel_written"] = report_excel_written
    if isinstance(report_output_exists, bool):
        attestation["output_exists"] = report_output_exists
    if isinstance(report_output_size_bytes, int):
        attestation["output_size_bytes"] = report_output_size_bytes
    result["output_attestation"] = attestation

    success_gates = all([
        delegate_status == "success",
        delegate_total_files >= 1,
        delegate_dry_run is False,
        status_counter.get("failed", 0) == 0,
        status_counter.get("partial", 0) == 0,
        attestation.get("excel_written") is True,
        attestation.get("output_exists") is True,
        int(attestation.get("output_size_bytes", 0) or 0) > 0,
    ])

    if success_gates:
        result["status"] = "success"
        result["summary"] = "Reviewed delegate reported success with sufficient structured evidence and a real XLSX output attestation."
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if delegate_status == "partial":
        result["status"] = "partial"
        result["summary"] = "Delegate returned a structured partial outcome; preserving partial status for reviewable best-effort flow."
        result["limitations"].append("Success-only evidence gates were not fully satisfied by the delegate report.")
        result["next_steps"].append("Review delegate stdout/stderr and report details to determine whether OCR support, PDF quality, or dependencies limited extraction.")
        result["next_steps"].append("If needed, rerun against a smaller known-good sample set or verify the reviewed delegate runtime prerequisites.")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result["status"] = "failed"
    result["summary"] = "Delegate did not provide sufficient structured evidence for success, and no contract-compliant partial outcome was established."
    result["limitations"].append("Wrapper will not treat exit code plus output-file existence alone as sufficient success evidence.")
    if delegate_status is None:
        result["limitations"].append("No canonical delegate JSON report was available from stdout or sidecar.")
    else:
        result["limitations"].append(f"Delegate status was {delegate_status!r}, which did not satisfy success gates.")
    result["next_steps"].append("Inspect the reviewed delegate CLI compatibility and JSON report fields status/total_files/status_counter/dry_run.")
    result["next_steps"].append("Ensure the delegate emits or writes contract-compliant JSON via stdout or --report-json sidecar.")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
