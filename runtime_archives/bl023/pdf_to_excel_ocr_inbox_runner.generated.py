#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_DESCRIPTION = (
    "Purpose: | Controlled Trello live preview smoke for openclaw-team. | "
    "Expected behavior: | - read-only Trello ingest | - preview creation smoke only | "
    "- no business execution cla..."
)


def _expand_path(value: str) -> Path:
    return Path(os.path.expanduser(value)).resolve()


def _repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_delegate(preferred_base_script: str) -> Path:
    candidate = Path(preferred_base_script)
    if candidate.is_absolute():
        return candidate
    repo_root = _repo_root_from_script()
    return (repo_root / candidate).resolve()


def _discover_pdfs(input_dir: Path) -> list[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(
        [p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"],
        key=lambda p: p.name.lower(),
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reviewable inbox runner for the repository PDF-to-Excel OCR helper."
    )
    parser.add_argument("--input-dir", default="~/Desktop/pdf样本")
    parser.add_argument(
        "--output-xlsx",
        default="artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx",
    )
    parser.add_argument("--ocr", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--origin-id", default="trello:69c24cd3c1a2359ddd7a1bf8")
    parser.add_argument(
        "--title",
        default="BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)",
    )
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument(
        "--labels",
        nargs="*",
        default=["best_effort", "evidence_backed", "readonly", "reviewable", "trello"],
    )
    parser.add_argument(
        "--preferred-base-script",
        default="artifacts/scripts/pdf_to_excel_ocr.py",
    )
    return parser.parse_args()


def _structured_summary(
    *,
    status: str,
    input_dir: Path,
    output_xlsx: Path,
    discovered_pdfs: list[Path],
    delegate_script: Path,
    origin_id: str,
    title: str,
    description: str,
    labels: list[str],
    dry_run: bool,
    ocr: str,
    produced: bool,
    delegate_exit_code: int | None,
    delegate_stdout: str | None,
    delegate_stderr: str | None,
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "origin_id": origin_id,
        "title": title,
        "description": description,
        "labels": labels,
        "input_dir": str(input_dir),
        "output_xlsx": str(output_xlsx),
        "ocr": ocr,
        "dry_run": dry_run,
        "delegate_script": str(delegate_script),
        "discovered_pdf_count": len(discovered_pdfs),
        "discovered_pdfs": [str(p) for p in discovered_pdfs],
        "produced_output": produced,
        "delegate_exit_code": delegate_exit_code,
        "reason": reason,
        "delegate_stdout": delegate_stdout,
        "delegate_stderr": delegate_stderr,
    }


def _print_summary_and_return(code: int, summary: dict[str, Any]) -> int:
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return code


def main() -> int:
    args = _parse_args()

    input_dir = _expand_path(args.input_dir)
    output_xlsx = _expand_path(args.output_xlsx)
    delegate_script = _resolve_delegate(args.preferred_base_script)
    discovered_pdfs = _discover_pdfs(input_dir)

    if output_xlsx.suffix.lower() != ".xlsx":
        summary = _structured_summary(
            status="failed",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            discovered_pdfs=discovered_pdfs,
            delegate_script=delegate_script,
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            dry_run=bool(args.dry_run),
            ocr=args.ocr,
            produced=False,
            delegate_exit_code=None,
            delegate_stdout=None,
            delegate_stderr=None,
            reason="Requested output path does not end with .xlsx; refusing mismatched workbook semantics.",
        )
        return _print_summary_and_return(2, summary)

    reviewed_delegate_rel = Path("artifacts/scripts/pdf_to_excel_ocr.py")
    if delegate_script != (_repo_root_from_script() / reviewed_delegate_rel).resolve():
        summary = _structured_summary(
            status="failed",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            discovered_pdfs=discovered_pdfs,
            delegate_script=delegate_script,
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            dry_run=bool(args.dry_run),
            ocr=args.ocr,
            produced=False,
            delegate_exit_code=None,
            delegate_stdout=None,
            delegate_stderr=None,
            reason="Readonly reviewable flow only permits delegation to artifacts/scripts/pdf_to_excel_ocr.py.",
        )
        return _print_summary_and_return(2, summary)

    if not delegate_script.exists():
        summary = _structured_summary(
            status="failed",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            discovered_pdfs=discovered_pdfs,
            delegate_script=delegate_script,
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            dry_run=bool(args.dry_run),
            ocr=args.ocr,
            produced=False,
            delegate_exit_code=None,
            delegate_stdout=None,
            delegate_stderr=None,
            reason="Preferred reviewed delegate script was not found.",
        )
        return _print_summary_and_return(2, summary)

    if args.dry_run:
        summary = _structured_summary(
            status="partial",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            discovered_pdfs=discovered_pdfs,
            delegate_script=delegate_script,
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            dry_run=True,
            ocr=args.ocr,
            produced=False,
            delegate_exit_code=None,
            delegate_stdout=None,
            delegate_stderr=None,
            reason="Dry-run requested; no XLSX artifact was produced.",
        )
        return _print_summary_and_return(0, summary)

    if not discovered_pdfs:
        summary = _structured_summary(
            status="partial",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            discovered_pdfs=discovered_pdfs,
            delegate_script=delegate_script,
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            dry_run=False,
            ocr=args.ocr,
            produced=False,
            delegate_exit_code=None,
            delegate_stdout=None,
            delegate_stderr=None,
            reason="No PDF files discovered in the provided input_dir.",
        )
        return _print_summary_and_return(0, summary)

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(delegate_script),
        "--input-dir",
        str(input_dir),
        "--output-xlsx",
        str(output_xlsx),
        "--ocr",
        str(args.ocr),
    ]

    completed = subprocess.run(cmd, capture_output=True, text=True)
    produced = output_xlsx.exists() and output_xlsx.is_file() and output_xlsx.stat().st_size > 0

    if completed.returncode == 0 and produced:
        status = "success"
        code = 0
        reason = "Delegate completed and a non-empty XLSX artifact is present."
    elif completed.returncode == 0 and not produced:
        status = "partial"
        code = 0
        reason = "Delegate reported success but no reviewable XLSX artifact was found."
    else:
        status = "failed"
        code = completed.returncode or 1
        reason = "Delegate execution failed."

    summary = _structured_summary(
        status=status,
        input_dir=input_dir,
        output_xlsx=output_xlsx,
        discovered_pdfs=discovered_pdfs,
        delegate_script=delegate_script,
        origin_id=args.origin_id,
        title=args.title,
        description=args.description,
        labels=list(args.labels),
        dry_run=False,
        ocr=args.ocr,
        produced=produced,
        delegate_exit_code=completed.returncode,
        delegate_stdout=completed.stdout,
        delegate_stderr=completed.stderr,
        reason=reason,
    )
    return _print_summary_and_return(code, summary)


if __name__ == "__main__":
    raise SystemExit(main())
