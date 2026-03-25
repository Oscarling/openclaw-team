#!/usr/bin/env python3
"""Local inbox-style wrapper for reviewed PDF->Excel OCR delegate.

This helper prefers delegating to the reviewed repository script
`artifacts/scripts/pdf_to_excel_ocr.py` and emits a structured JSON summary
suitable for reviewable smoke execution.

Contract highlights implemented here:
- parameter-driven `input_dir` and `output_xlsx`
- portable relative delegate resolution from repository/script location
- bounded delegate subprocess timeout
- partial outcome for dry-run or zero discovered PDFs
- stronger success evidence from delegate JSON report fields
- parse delegate JSON from stdout and/or `--report-json` sidecar
- no mismatched non-XLSX content written to `.xlsx` outputs by this wrapper
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
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DELEGATE_REL = "artifacts/scripts/pdf_to_excel_ocr.py"
DEFAULT_TIMEOUT_SECONDS = 900


@dataclass
class DiscoveryResult:
    total_pdfs: int
    files: List[Path]


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def resolve_repo_relative(path_str: str) -> Path:
    candidate = Path(path_str)
    if candidate.is_absolute():
        return candidate
    return (REPO_ROOT / candidate).resolve()


def discover_pdfs(input_dir: Path) -> DiscoveryResult:
    # Use recursive discovery to stay aligned with common delegate behavior for folder-based processing.
    files = sorted(p for p in input_dir.rglob("*.pdf") if p.is_file())
    return DiscoveryResult(total_pdfs=len(files), files=files)


def extract_json_object_from_text(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    stripped = text.strip()
    if not stripped:
        return None

    # First try whole payload.
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Fallback: scan lines from bottom to top for a JSON object.
    for line in reversed([ln.strip() for ln in stripped.splitlines() if ln.strip()]):
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def evidence_status_from_delegate(report: Dict[str, Any]) -> str:
    status = str(report.get("status", "")).strip().lower()
    total_files = report.get("total_files")
    status_counter = report.get("status_counter") or {}
    dry_run = bool(report.get("dry_run", False))

    try:
        total = int(total_files)
    except Exception:
        total = 0

    if dry_run:
        return "partial"
    if total <= 0:
        return "partial"

    if status == "success":
        failed = 0
        if isinstance(status_counter, dict):
            try:
                failed = sum(
                    int(v)
                    for k, v in status_counter.items()
                    if str(k).strip().lower() in {"failed", "error", "errors", "timeout"}
                )
            except Exception:
                failed = 0
        return "success" if failed == 0 else "partial"

    if status in {"partial", "failed"}:
        return status

    return "partial"


def build_summary(
    *,
    status: str,
    input_dir: Path,
    output_xlsx: Path,
    params: argparse.Namespace,
    discovery: DiscoveryResult,
    delegate_path: Path,
    delegated: bool,
    delegate_report: Optional[Dict[str, Any]],
    delegate_exit_code: Optional[int],
    stdout_text: str,
    stderr_text: str,
    extra_notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "status": status,
        "request": {
            "origin_id": params.origin_id,
            "title": params.title,
            "description": params.description,
            "labels": params.labels,
            "ocr": params.ocr,
            "dry_run": params.dry_run,
            "input_dir": str(input_dir),
            "output_xlsx": str(output_xlsx),
        },
        "traceability": {
            "wrapper_script": str(Path(__file__).resolve()),
            "delegate_script": str(delegate_path),
        },
        "discovery": {
            "input_dir": str(input_dir),
            "total_pdfs": discovery.total_pdfs,
            "sample_files": [str(p) for p in discovery.files[:10]],
            "recursive": True,
        },
        "execution": {
            "delegated": delegated,
            "delegate_exit_code": delegate_exit_code,
            "timeout_seconds": params.delegate_timeout,
            "output_exists": output_xlsx.exists(),
            "output_size": output_xlsx.stat().st_size if output_xlsx.exists() else 0,
        },
        "delegate_report": delegate_report,
        "logs": {
            "stdout_tail": stdout_text[-4000:],
            "stderr_tail": stderr_text[-4000:],
        },
        "notes": extra_notes or [],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reviewable inbox runner for PDF-to-Excel OCR delegate")
    parser.add_argument("--input-dir", required=True, help="Directory containing PDF files")
    parser.add_argument("--output-xlsx", required=True, help="Target XLSX output path")
    parser.add_argument("--ocr", default="auto", help="OCR mode to pass through when supported")
    parser.add_argument("--dry-run", action="store_true", help="Reviewable dry-run; returns partial")
    parser.add_argument("--origin-id", default="", help="Source origin id for traceability")
    parser.add_argument("--title", default="", help="Request title")
    parser.add_argument("--description", default="", help="Request description")
    parser.add_argument("--labels", nargs="*", default=[], help="Traceability labels")
    parser.add_argument(
        "--preferred-base-script",
        default=DEFAULT_DELEGATE_REL,
        help="Preferred reviewed delegate script path",
    )
    parser.add_argument(
        "--delegate-timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Explicit subprocess timeout in seconds",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="Optional path to write wrapper structured summary JSON",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_dir = expand_path(args.input_dir)
    output_xlsx = expand_path(args.output_xlsx)
    delegate_path = resolve_repo_relative(args.preferred_base_script)

    notes: List[str] = []

    if output_xlsx.suffix.lower() != ".xlsx":
        notes.append("Requested output path is not .xlsx; wrapper expects real XLSX target semantics.")

    if not input_dir.exists() or not input_dir.is_dir():
        summary = build_summary(
            status="failed",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            params=args,
            discovery=DiscoveryResult(total_pdfs=0, files=[]),
            delegate_path=delegate_path,
            delegated=False,
            delegate_report=None,
            delegate_exit_code=None,
            stdout_text="",
            stderr_text="Input directory does not exist or is not a directory.",
            extra_notes=notes + ["Input directory validation failed."],
        )
        payload = json.dumps(summary, ensure_ascii=False, indent=2)
        if args.summary_json:
            summary_path = expand_path(args.summary_json)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(payload, encoding="utf-8")
        print(payload)
        return 2

    discovery = discover_pdfs(input_dir)

    if args.dry_run:
        summary = build_summary(
            status="partial",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            params=args,
            discovery=discovery,
            delegate_path=delegate_path,
            delegated=False,
            delegate_report=None,
            delegate_exit_code=None,
            stdout_text="",
            stderr_text="",
            extra_notes=notes + ["Dry-run short-circuit: delegate not executed."],
        )
        payload = json.dumps(summary, ensure_ascii=False, indent=2)
        if args.summary_json:
            summary_path = expand_path(args.summary_json)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(payload, encoding="utf-8")
        print(payload)
        return 0

    if discovery.total_pdfs == 0:
        summary = build_summary(
            status="partial",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            params=args,
            discovery=discovery,
            delegate_path=delegate_path,
            delegated=False,
            delegate_report=None,
            delegate_exit_code=None,
            stdout_text="",
            stderr_text="",
            extra_notes=notes + ["No PDF files discovered; nothing delegated."],
        )
        payload = json.dumps(summary, ensure_ascii=False, indent=2)
        if args.summary_json:
            summary_path = expand_path(args.summary_json)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(payload, encoding="utf-8")
        print(payload)
        return 0

    if not delegate_path.is_file():
        summary = build_summary(
            status="failed",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            params=args,
            discovery=discovery,
            delegate_path=delegate_path,
            delegated=False,
            delegate_report=None,
            delegate_exit_code=None,
            stdout_text="",
            stderr_text="Reviewed delegate script not found.",
            extra_notes=notes + ["Readonly reviewable flow only delegates to reviewed repository script."],
        )
        payload = json.dumps(summary, ensure_ascii=False, indent=2)
        if args.summary_json:
            summary_path = expand_path(args.summary_json)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(payload, encoding="utf-8")
        print(payload)
        return 2

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_runner_") as tmpdir:
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
        if args.dry_run:
            cmd.append("--dry-run")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=args.delegate_timeout,
                cwd=str(REPO_ROOT),
                check=False,
            )
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""
            delegate_report = extract_json_object_from_text(stdout_text) or load_json_file(report_path)
            final_status = "failed"
            if delegate_report is not None:
                final_status = evidence_status_from_delegate(delegate_report)
            elif proc.returncode == 0:
                notes.append("Delegate exited zero but did not provide canonical JSON evidence; wrapper does not upgrade to success.")
                final_status = "partial" if output_xlsx.exists() else "failed"

            summary = build_summary(
                status=final_status,
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                params=args,
                discovery=discovery,
                delegate_path=delegate_path,
                delegated=True,
                delegate_report=delegate_report,
                delegate_exit_code=proc.returncode,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                extra_notes=notes,
            )
            payload = json.dumps(summary, ensure_ascii=False, indent=2)
            if args.summary_json:
                summary_path = expand_path(args.summary_json)
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(payload, encoding="utf-8")
            print(payload)
            return 0 if final_status in {"success", "partial"} else 2

        except subprocess.TimeoutExpired as exc:
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
            summary = build_summary(
                status="failed",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                params=args,
                discovery=discovery,
                delegate_path=delegate_path,
                delegated=True,
                delegate_report=None,
                delegate_exit_code=None,
                stdout_text=stdout_text if isinstance(stdout_text, str) else "",
                stderr_text=(stderr_text if isinstance(stderr_text, str) else "") + "\nDelegate timed out.",
                extra_notes=notes + ["Delegate subprocess timed out before producing reviewable completion evidence."],
            )
            payload = json.dumps(summary, ensure_ascii=False, indent=2)
            if args.summary_json:
                summary_path = expand_path(args.summary_json)
                summary_path.parent.mkdir(parents=True, exist_ok=True)
                summary_path.write_text(payload, encoding="utf-8")
            print(payload)
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
