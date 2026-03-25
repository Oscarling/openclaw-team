#!/usr/bin/env python3
"""Reviewed inbox wrapper for best-effort PDF-to-Excel OCR conversion.

This wrapper is intentionally conservative:
- reuses the reviewed repository delegate when available
- passes through dry-run semantics instead of short-circuiting
- prefers delegate sidecar JSON report evidence via --report-json
- treats zero discovered PDFs or dry-run as reviewable partial outcomes
- only reports success when strong delegate evidence is present
- bounds delegate execution with an explicit timeout

It is designed for readonly governed preview flows where no external/Trello
writeback occurs. Local filesystem writes may still occur when dry_run=false.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_TIMEOUT_SECONDS = 900


@dataclass
class DiscoveryResult:
    pdf_files: List[str]
    count: int


@dataclass
class DelegateRunResult:
    returncode: Optional[int]
    timed_out: bool
    stdout: str
    stderr: str
    report: Optional[Dict[str, Any]]
    command: List[str]
    report_path: str


DESCRIPTION_DEFAULT = (
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


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_delegate(preferred_base_script: Optional[str]) -> Path:
    repo_root = _repo_root()
    candidates: List[Path] = []
    if preferred_base_script:
        p = Path(preferred_base_script)
        if p.is_absolute():
            candidates.append(p)
        else:
            candidates.append((repo_root / p).resolve())
            candidates.append((Path(__file__).resolve().parent / p.name).resolve())
    candidates.append((repo_root / "artifacts/scripts/pdf_to_excel_ocr.py").resolve())

    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Reviewed delegate script not found. Expected artifacts/scripts/pdf_to_excel_ocr.py or compatible preferred_base_script."
    )


def _expand_input_dir(input_dir: str) -> Path:
    return Path(os.path.expanduser(input_dir)).resolve()


def _discover_pdfs(input_dir: Path) -> DiscoveryResult:
    if not input_dir.exists() or not input_dir.is_dir():
        return DiscoveryResult(pdf_files=[], count=0)
    pdfs = sorted(str(p) for p in input_dir.rglob("*.pdf") if p.is_file())
    return DiscoveryResult(pdf_files=pdfs, count=len(pdfs))


def _parse_json_maybe(text: str) -> Optional[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _load_report(report_path: Path, stdout: str) -> Optional[Dict[str, Any]]:
    if report_path.exists():
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return _parse_json_maybe(stdout)


def _build_delegate_command(
    delegate_script: Path,
    input_dir: Path,
    output_xlsx: Path,
    ocr: str,
    dry_run: bool,
    report_path: Path,
) -> List[str]:
    cmd = [
        sys.executable,
        str(delegate_script),
        "--input-dir",
        str(input_dir),
        "--output-xlsx",
        str(output_xlsx),
        "--ocr",
        ocr,
        "--report-json",
        str(report_path),
    ]
    if dry_run:
        cmd.append("--dry-run")
    return cmd


def _run_delegate(
    delegate_script: Path,
    input_dir: Path,
    output_xlsx: Path,
    ocr: str,
    dry_run: bool,
    timeout_seconds: int,
) -> DelegateRunResult:
    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_ocr_runner_") as tmpdir:
        report_path = Path(tmpdir) / "delegate_report.json"
        cmd = _build_delegate_command(delegate_script, input_dir, output_xlsx, ocr, dry_run, report_path)
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            report = _load_report(report_path, proc.stdout)
            return DelegateRunResult(
                returncode=proc.returncode,
                timed_out=False,
                stdout=proc.stdout,
                stderr=proc.stderr,
                report=report,
                command=cmd,
                report_path=str(report_path),
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", errors="replace") if exc.stdout else "")
            stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", errors="replace") if exc.stderr else "")
            report = _load_report(report_path, stdout)
            return DelegateRunResult(
                returncode=None,
                timed_out=True,
                stdout=stdout,
                stderr=stderr,
                report=report,
                command=cmd,
                report_path=str(report_path),
            )


def _status_counter(report: Dict[str, Any]) -> Dict[str, int]:
    raw = report.get("status_counter")
    if isinstance(raw, dict):
        result = {}
        for key, value in raw.items():
            try:
                result[str(key)] = int(value)
            except Exception:
                continue
        return result
    return {}


def _is_success_evidence(report: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    counter = _status_counter(report)
    if report.get("status") != "success":
        reasons.append("delegate status is not success")
    if int(report.get("total_files", 0) or 0) < 1:
        reasons.append("delegate total_files < 1")
    if bool(report.get("dry_run", False)):
        reasons.append("delegate dry_run is true")
    if int(counter.get("failed", 0)) != 0:
        reasons.append("delegate status_counter.failed != 0")
    if int(counter.get("partial", 0)) != 0:
        reasons.append("delegate status_counter.partial != 0")
    if report.get("excel_written") is not True:
        reasons.append("delegate excel_written is not true")
    if report.get("output_exists") is not True:
        reasons.append("delegate output_exists is not true")
    if int(report.get("output_size_bytes", 0) or 0) <= 0:
        reasons.append("delegate output_size_bytes <= 0")

    ocr_runtime_status = str(report.get("ocr_runtime_status", "")).strip().lower()
    if ocr_runtime_status in {"blocked", "partial"}:
        reasons.append(f"delegate ocr_runtime_status={ocr_runtime_status} is insufficient for success")

    return (len(reasons) == 0, reasons)


def _json_print(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Best-effort reviewed inbox wrapper for PDF-to-Excel OCR.")
    parser.add_argument("--input-dir", default="~/Desktop/pdf样本")
    parser.add_argument("--output-xlsx", default="artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx")
    parser.add_argument("--ocr", default="auto", choices=["auto", "on", "off"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--origin-id", default="trello:69c24cd3c1a2359ddd7a1bf8")
    parser.add_argument(
        "--title",
        default="BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)",
    )
    parser.add_argument("--description", default=DESCRIPTION_DEFAULT)
    parser.add_argument("--preferred-base-script", default="artifacts/scripts/pdf_to_excel_ocr.py")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    input_dir = _expand_input_dir(args.input_dir)
    output_xlsx = Path(args.output_xlsx)
    if not output_xlsx.is_absolute():
        output_xlsx = (_repo_root() / output_xlsx).resolve()

    summary: Dict[str, Any] = {
        "status": "failed",
        "origin_id": args.origin_id,
        "title": args.title,
        "description": args.description,
        "mode": "readonly-reviewable",
        "readonly_semantics": "No external/Trello writeback is performed by this wrapper. Local filesystem output may occur when dry_run=false.",
        "input_dir": str(input_dir),
        "output_xlsx": str(output_xlsx),
        "ocr": args.ocr,
        "dry_run": bool(args.dry_run),
        "timeout_seconds": int(args.timeout_seconds),
        "traceability": {
            "backlog": "BL-20260324-014",
            "blocker_context": "BL-20260324-015",
            "source_origin_id": args.origin_id,
        },
    }

    if output_xlsx.suffix.lower() != ".xlsx":
        summary.update(
            {
                "status": "failed",
                "limitations": ["output_xlsx must end with .xlsx to preserve workbook semantics"],
                "next_steps": ["Provide an .xlsx output path and rerun."],
            }
        )
        _json_print(summary)
        return 2

    discovery = _discover_pdfs(input_dir)
    summary["preflight"] = {
        "pdf_discovery_mode": "recursive_rglob",
        "discovered_pdf_count": discovery.count,
        "discovered_pdf_examples": discovery.pdf_files[:20],
    }

    try:
        delegate_script = _resolve_delegate(args.preferred_base_script)
    except FileNotFoundError as exc:
        summary.update(
            {
                "status": "failed",
                "limitations": [str(exc)],
                "next_steps": [
                    "Restore the reviewed delegate artifacts/scripts/pdf_to_excel_ocr.py or pass a compatible preferred base script.",
                ],
            }
        )
        _json_print(summary)
        return 2

    summary["delegate"] = {
        "script": str(delegate_script),
        "report_handoff": "--report-json sidecar preferred; stdout JSON fallback",
    }

    if discovery.count == 0:
        summary.update(
            {
                "status": "partial",
                "limitations": ["No PDF files were discovered under input_dir; no XLSX artifact was produced."],
                "next_steps": [
                    "Place one or more .pdf files under the input directory and rerun.",
                    "Confirm the input path exists and contains discoverable PDFs.",
                ],
                "runtime_summary": {
                    "produced_output": False,
                    "external_writeback": False,
                },
            }
        )
        _json_print(summary)
        return 0

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    delegate_result = _run_delegate(
        delegate_script=delegate_script,
        input_dir=input_dir,
        output_xlsx=output_xlsx,
        ocr=args.ocr,
        dry_run=bool(args.dry_run),
        timeout_seconds=int(args.timeout_seconds),
    )

    summary["delegate_run"] = {
        "command": delegate_result.command,
        "returncode": delegate_result.returncode,
        "timed_out": delegate_result.timed_out,
        "report_path": delegate_result.report_path,
        "stderr_tail": delegate_result.stderr[-4000:],
    }

    report = delegate_result.report or {}
    summary["delegate_report"] = report

    if delegate_result.timed_out:
        status = "partial" if report.get("status") == "partial" else "failed"
        summary.update(
            {
                "status": status,
                "limitations": [
                    f"Delegate execution exceeded timeout of {args.timeout_seconds} seconds.",
                ],
                "next_steps": [
                    "Retry with a smaller input set or a higher timeout if justified.",
                    "Inspect delegate stderr/stdout evidence for progress before timeout.",
                ],
                "runtime_summary": {
                    "produced_output": bool(report.get("output_exists", False)),
                    "external_writeback": False,
                },
            }
        )
        _json_print(summary)
        return 1 if status == "failed" else 0

    if not report:
        summary.update(
            {
                "status": "failed",
                "limitations": [
                    "Reviewed delegate did not provide a usable structured JSON report via sidecar or stdout.",
                ],
                "next_steps": [
                    "Inspect the reviewed delegate CLI compatibility for --report-json.",
                    "Review delegate stdout/stderr and ensure report emission matches the expected schema.",
                ],
                "runtime_summary": {
                    "produced_output": False,
                    "external_writeback": False,
                },
            }
        )
        _json_print(summary)
        return 2

    delegate_status = str(report.get("status", "failed"))
    success_ok, success_reasons = _is_success_evidence(report)
    output_exists = bool(report.get("output_exists", False))
    output_size_bytes = int(report.get("output_size_bytes", 0) or 0)
    ocr_runtime_status = str(report.get("ocr_runtime_status", "")).strip().lower()

    runtime_summary = {
        "produced_output": output_exists and output_size_bytes > 0,
        "output_exists": output_exists,
        "output_size_bytes": output_size_bytes,
        "excel_written": bool(report.get("excel_written", False)),
        "external_writeback": False,
        "total_files": int(report.get("total_files", 0) or 0),
        "delegate_status": delegate_status,
        "ocr_runtime_status": ocr_runtime_status or None,
    }

    if args.dry_run:
        summary.update(
            {
                "status": "partial",
                "limitations": [
                    "Dry-run was requested and delegated explicitly; no success claim is made for artifact production.",
                ],
                "next_steps": [
                    "Rerun without --dry-run to attempt real XLSX generation.",
                ],
                "runtime_summary": runtime_summary,
            }
        )
        _json_print(summary)
        return 0

    if delegate_status == "partial":
        limitations = [
            "Delegate reported a partial outcome; wrapper preserves partial status for reviewable best-effort flow.",
        ]
        if ocr_runtime_status in {"blocked", "partial"}:
            limitations.append(f"OCR sufficiency limitation reported by delegate: {ocr_runtime_status}.")
        if success_reasons:
            limitations.extend(success_reasons)
        summary.update(
            {
                "status": "partial",
                "limitations": limitations,
                "next_steps": [
                    "Review delegate_report for file-level limitations and OCR constraints.",
                    "If OCR is required, ensure OCR runtime dependencies are available and rerun.",
                    "Confirm source PDFs are machine-readable enough for the reviewed pipeline.",
                ],
                "runtime_summary": runtime_summary,
            }
        )
        _json_print(summary)
        return 0

    if success_ok:
        summary.update(
            {
                "status": "success",
                "limitations": [],
                "next_steps": [],
                "runtime_summary": runtime_summary,
            }
        )
        _json_print(summary)
        return 0

    status = "partial" if delegate_status == "success" and (ocr_runtime_status in {"blocked", "partial"} or report.get("dry_run") is True) else "failed"
    summary.update(
        {
            "status": status,
            "limitations": success_reasons or ["Delegate outcome did not satisfy wrapper success evidence gates."],
            "next_steps": [
                "Inspect delegate_report and delegate stderr for the failing evidence conditions.",
                "Rerun after correcting OCR/runtime prerequisites or input quality issues.",
            ],
            "runtime_summary": runtime_summary,
        }
    )
    _json_print(summary)
    return 0 if status == "partial" else 2


if __name__ == "__main__":
    raise SystemExit(main())
