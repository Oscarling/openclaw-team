#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_DELEGATE_RELATIVE = "artifacts/scripts/pdf_to_excel_ocr.py"
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
DEFAULT_ORIGIN_ID = "trello:69c24cd3c1a2359ddd7a1bf8"
DEFAULT_LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _expand_path(value: str) -> Path:
    return Path(os.path.expanduser(value)).resolve()


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _discover_pdfs(input_dir: Path) -> list[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(
        [p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"],
        key=lambda p: str(p).lower(),
    )


def _resolve_delegate(preferred: str | None) -> Path:
    script_dir = Path(__file__).resolve().parent
    repo_root = _repo_root()
    candidates: list[Path] = []
    if preferred:
        pref_path = Path(preferred)
        if pref_path.is_absolute():
            candidates.append(pref_path)
        else:
            candidates.append((repo_root / pref_path).resolve())
            candidates.append((script_dir / pref_path).resolve())
    default_path = Path(DEFAULT_DELEGATE_RELATIVE)
    candidates.append((repo_root / default_path).resolve())
    candidates.append((script_dir / default_path).resolve())
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists() and candidate.is_file():
            return candidate
    return candidates[0]


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        if path.exists() and path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _parse_stdout_json(stdout: str) -> dict[str, Any] | None:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    for line in reversed([ln.strip() for ln in text.splitlines() if ln.strip()]):
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def _status_counter(report: dict[str, Any]) -> dict[str, int]:
    raw = report.get("status_counter")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, int] = {}
    for key, value in raw.items():
        try:
            result[str(key)] = int(value)
        except Exception:
            continue
    return result


def _int_field(report: dict[str, Any], field: str) -> int | None:
    value = report.get(field)
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _bool_field(report: dict[str, Any], field: str) -> bool | None:
    value = report.get(field)
    if isinstance(value, bool):
        return value
    return None


def _build_summary(
    *,
    wrapper_status: str,
    message: str,
    input_dir: Path,
    output_xlsx: Path,
    delegate_path: Path,
    discovered_pdfs: list[Path],
    dry_run: bool,
    timeout_seconds: int,
    origin_id: str,
    title: str,
    description: str,
    labels: list[str],
    delegate_cmd: list[str] | None = None,
    delegate_exit_code: int | None = None,
    delegate_report_source: str | None = None,
    delegate_report: dict[str, Any] | None = None,
    limitations: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> dict[str, Any]:
    output_exists = output_xlsx.exists() and output_xlsx.is_file()
    output_size = output_xlsx.stat().st_size if output_exists else 0
    return {
        "status": wrapper_status,
        "message": message,
        "origin_id": origin_id,
        "title": title,
        "description": description,
        "labels": labels,
        "input_dir": str(input_dir),
        "output_xlsx": str(output_xlsx),
        "output_xlsx_suffix": output_xlsx.suffix.lower(),
        "output_exists": output_exists,
        "output_size_bytes": output_size,
        "delegate_script": str(delegate_path),
        "delegate_command": delegate_cmd or [],
        "delegate_exit_code": delegate_exit_code,
        "delegate_report_source": delegate_report_source,
        "delegate_report": delegate_report,
        "dry_run": dry_run,
        "timeout_seconds": timeout_seconds,
        "discovered_pdf_count": len(discovered_pdfs),
        "discovered_pdfs": [str(p) for p in discovered_pdfs],
        "limitations": limitations or [],
        "next_steps": next_steps or [],
        "runtime_summary": {
            "produced_real_xlsx": bool(output_exists and output_size > 0 and output_xlsx.suffix.lower() == ".xlsx"),
            "reviewable": True,
            "readonly_flow": True,
            "best_effort": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly reviewable inbox wrapper for PDF-to-Excel OCR delegate.")
    parser.add_argument("--input-dir", default="~/Desktop/pdf样本")
    parser.add_argument("--output-xlsx", default="artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx")
    parser.add_argument("--ocr", default="auto")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--origin-id", default=DEFAULT_ORIGIN_ID)
    parser.add_argument("--title", default=DEFAULT_TITLE)
    parser.add_argument("--description", default=DEFAULT_DESCRIPTION)
    parser.add_argument("--labels", nargs="*", default=DEFAULT_LABELS)
    parser.add_argument("--preferred-base-script", default=DEFAULT_DELEGATE_RELATIVE)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    input_dir = _expand_path(args.input_dir)
    output_xlsx = _expand_path(args.output_xlsx)
    delegate_path = _resolve_delegate(args.preferred_base_script)
    discovered_pdfs = _discover_pdfs(input_dir)

    if output_xlsx.suffix.lower() != ".xlsx":
        summary = _build_summary(
            wrapper_status="failed",
            message="Refusing to proceed because output_xlsx does not end with .xlsx; honest failure preserves workbook format contract.",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            delegate_path=delegate_path,
            discovered_pdfs=discovered_pdfs,
            dry_run=bool(args.dry_run),
            timeout_seconds=int(args.timeout_seconds),
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            limitations=["Requested output path is not a .xlsx target."],
            next_steps=["Provide an output path ending in .xlsx and rerun."],
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
        return 2

    if not delegate_path.exists() or not delegate_path.is_file():
        summary = _build_summary(
            wrapper_status="failed",
            message="Reviewed delegate script was not found; refusing to broaden behavior beyond the approved repository implementation.",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            delegate_path=delegate_path,
            discovered_pdfs=discovered_pdfs,
            dry_run=bool(args.dry_run),
            timeout_seconds=int(args.timeout_seconds),
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            limitations=["Reviewed delegate artifacts/scripts/pdf_to_excel_ocr.py is unavailable from the resolved repository/script paths."],
            next_steps=["Restore the reviewed delegate script and rerun the wrapper."],
        )
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
        return 2

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_ocr_runner_") as tmpdir:
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
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(1, int(args.timeout_seconds)),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            summary = _build_summary(
                wrapper_status="failed",
                message="Delegate execution timed out before completion.",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                delegate_path=delegate_path,
                discovered_pdfs=discovered_pdfs,
                dry_run=bool(args.dry_run),
                timeout_seconds=int(args.timeout_seconds),
                origin_id=args.origin_id,
                title=args.title,
                description=args.description,
                labels=list(args.labels),
                delegate_cmd=cmd,
                delegate_exit_code=None,
                delegate_report_source=None,
                delegate_report=None,
                limitations=["Delegate subprocess exceeded the explicit timeout bound.", f"Timeout seconds: {int(args.timeout_seconds)}"],
                next_steps=["Inspect the input PDFs and delegate performance.", "Retry with a larger timeout only if justified by review."],
            )
            summary["delegate_stdout_tail"] = (exc.stdout or "")[-4000:]
            summary["delegate_stderr_tail"] = (exc.stderr or "")[-4000:]
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
            return 2

        report = _safe_read_json(report_path)
        report_source = "sidecar_json" if report is not None else None
        if report is None:
            report = _parse_stdout_json(completed.stdout)
            if report is not None:
                report_source = "stdout_json_fallback"

        limitations: list[str] = []
        next_steps: list[str] = []

        if not isinstance(report, dict):
            limitations.append("Delegate did not provide a readable structured JSON report via sidecar or stdout fallback.")
            next_steps.append("Inspect delegate stdout/stderr and verify reviewed script support for --report-json.")
            summary = _build_summary(
                wrapper_status="failed",
                message="Structured delegate evidence was unavailable, so success cannot be claimed honestly.",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                delegate_path=delegate_path,
                discovered_pdfs=discovered_pdfs,
                dry_run=bool(args.dry_run),
                timeout_seconds=int(args.timeout_seconds),
                origin_id=args.origin_id,
                title=args.title,
                description=args.description,
                labels=list(args.labels),
                delegate_cmd=cmd,
                delegate_exit_code=completed.returncode,
                delegate_report_source=report_source,
                delegate_report=None,
                limitations=limitations,
                next_steps=next_steps,
            )
            summary["delegate_stdout_tail"] = (completed.stdout or "")[-4000:]
            summary["delegate_stderr_tail"] = (completed.stderr or "")[-4000:]
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
            return 2

        delegate_status = str(report.get("status", "")).strip().lower()
        total_files = _int_field(report, "total_files")
        delegate_dry_run = _bool_field(report, "dry_run")
        counters = _status_counter(report)
        failed_count = int(counters.get("failed", 0))
        partial_count = int(counters.get("partial", 0))
        excel_written = _bool_field(report, "excel_written")
        output_exists = _bool_field(report, "output_exists")
        output_size_bytes = _int_field(report, "output_size_bytes")

        success_evidence = all(
            [
                delegate_status == "success",
                total_files is not None and total_files >= 1,
                delegate_dry_run is False,
                failed_count == 0,
                partial_count == 0,
                excel_written is True,
                output_exists is True,
                output_size_bytes is not None and output_size_bytes > 0,
            ]
        )

        if delegate_status == "success" and success_evidence:
            summary = _build_summary(
                wrapper_status="success",
                message="Delegate reported contract-complete success with strong workbook evidence.",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                delegate_path=delegate_path,
                discovered_pdfs=discovered_pdfs,
                dry_run=bool(args.dry_run),
                timeout_seconds=int(args.timeout_seconds),
                origin_id=args.origin_id,
                title=args.title,
                description=args.description,
                labels=list(args.labels),
                delegate_cmd=cmd,
                delegate_exit_code=completed.returncode,
                delegate_report_source=report_source,
                delegate_report=report,
                limitations=[],
                next_steps=["Review the generated XLSX workbook content for smoke validation evidence."],
            )
            summary["delegate_stdout_tail"] = (completed.stdout or "")[-4000:]
            summary["delegate_stderr_tail"] = (completed.stderr or "")[-4000:]
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
            return 0

        if delegate_status == "partial":
            if bool(args.dry_run):
                limitations.append("Delegate ran in dry-run mode; preview evidence is reviewable but not a completed XLSX production claim.")
            if total_files == 0 or len(discovered_pdfs) == 0:
                limitations.append("No PDF files were discovered for processing.")
            if partial_count > 0:
                limitations.append(f"Delegate reported partial item count: {partial_count}.")
            if failed_count > 0:
                limitations.append(f"Delegate also reported failed item count: {failed_count}.")
            next_steps.extend(
                [
                    "Review the delegate report for file-level limitations.",
                    "If real conversion is required, provide accessible PDFs and rerun without --dry-run.",
                ]
            )
            summary = _build_summary(
                wrapper_status="partial",
                message="Delegate returned a structured partial outcome; wrapper preserves it as reviewable partial rather than overstating success.",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                delegate_path=delegate_path,
                discovered_pdfs=discovered_pdfs,
                dry_run=bool(args.dry_run),
                timeout_seconds=int(args.timeout_seconds),
                origin_id=args.origin_id,
                title=args.title,
                description=args.description,
                labels=list(args.labels),
                delegate_cmd=cmd,
                delegate_exit_code=completed.returncode,
                delegate_report_source=report_source,
                delegate_report=report,
                limitations=limitations,
                next_steps=next_steps,
            )
            summary["delegate_stdout_tail"] = (completed.stdout or "")[-4000:]
            summary["delegate_stderr_tail"] = (completed.stderr or "")[-4000:]
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
            return 0

        if delegate_status == "success" and not success_evidence:
            limitations.append("Delegate labeled the run as success, but strong evidence gates required by the wrapper were not fully satisfied.")
            if total_files is None or total_files < 1:
                limitations.append("Missing or insufficient total_files evidence.")
            if delegate_dry_run is not False:
                limitations.append("Delegate dry_run evidence was not false.")
            if failed_count != 0:
                limitations.append(f"Delegate reported failed count {failed_count}, which blocks wrapper success.")
            if partial_count != 0:
                limitations.append(f"Delegate reported partial count {partial_count}, which blocks wrapper success.")
            if excel_written is not True:
                limitations.append("excel_written=true attestation was absent.")
            if output_exists is not True:
                limitations.append("output_exists=true attestation was absent.")
            if output_size_bytes is None or output_size_bytes <= 0:
                limitations.append("output_size_bytes>0 attestation was absent.")
            next_steps.extend(
                [
                    "Inspect the delegate report and workbook output before treating the run as complete.",
                    "Adjust the reviewed delegate so it emits the required evidence fields if appropriate.",
                ]
            )
            summary = _build_summary(
                wrapper_status="failed",
                message="Wrapper refused to claim success because the delegate evidence did not meet the required success gates.",
                input_dir=input_dir,
                output_xlsx=output_xlsx,
                delegate_path=delegate_path,
                discovered_pdfs=discovered_pdfs,
                dry_run=bool(args.dry_run),
                timeout_seconds=int(args.timeout_seconds),
                origin_id=args.origin_id,
                title=args.title,
                description=args.description,
                labels=list(args.labels),
                delegate_cmd=cmd,
                delegate_exit_code=completed.returncode,
                delegate_report_source=report_source,
                delegate_report=report,
                limitations=limitations,
                next_steps=next_steps,
            )
            summary["delegate_stdout_tail"] = (completed.stdout or "")[-4000:]
            summary["delegate_stderr_tail"] = (completed.stderr or "")[-4000:]
            print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
            return 2

        limitations.append(f"Delegate returned status '{delegate_status or 'unknown'}', which is not sufficient for wrapper success.")
        if completed.returncode != 0:
            limitations.append(f"Delegate subprocess exit code: {completed.returncode}.")
        next_steps.extend(
            [
                "Review delegate stdout/stderr and structured report for the root cause.",
                "Correct the input set or delegate behavior, then rerun the smoke wrapper.",
            ]
        )
        summary = _build_summary(
            wrapper_status="failed",
            message="Delegate did not produce a contract-complete success or reviewable partial outcome.",
            input_dir=input_dir,
            output_xlsx=output_xlsx,
            delegate_path=delegate_path,
            discovered_pdfs=discovered_pdfs,
            dry_run=bool(args.dry_run),
            timeout_seconds=int(args.timeout_seconds),
            origin_id=args.origin_id,
            title=args.title,
            description=args.description,
            labels=list(args.labels),
            delegate_cmd=cmd,
            delegate_exit_code=completed.returncode,
            delegate_report_source=report_source,
            delegate_report=report,
            limitations=limitations,
            next_steps=next_steps,
        )
        summary["delegate_stdout_tail"] = (completed.stdout or "")[-4000:]
        summary["delegate_stderr_tail"] = (completed.stderr or "")[-4000:]
        print(json.dumps(summary, ensure_ascii=False, indent=2, default=_json_default))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
