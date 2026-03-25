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

DEFAULT_TIMEOUT_SECONDS = 900
REQUEST_PAYLOAD = {
    "origin_id": "trello:69c24cd3c1a2359ddd7a1bf8",
    "title": "BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)",
    "description": "Purpose: | Controlled Trello live preview smoke for openclaw-team. | Expected behavior: | - read-only Trello ingest | - preview creation smoke only | - no business execution claim | - no Trello writeback expected in this step | Traceability: | - backlog: BL-20260324-014 | - blocker context: BL-20260324-015 | - created_by: Oscarling | - created_at: 2026-03-24 Asia/Shanghai | Note: | This card is only for governed smoke verification and should remain open until the smoke is finished.",
    "labels": ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"],
    "source": {
        "kind": "local_inbox",
        "provider": "trello",
        "mode": "readonly",
        "card_id": "69c24cd3c1a2359ddd7a1bf8",
        "board_id": "69be462743bfa0038ca10f7a",
        "list_id": "69be462743bfa0038ca10f8f",
        "inbox_file": "trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl063-001.json",
        "regeneration_token": "regen-20260325-bl063-001"
    }
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _expand_path(raw: str) -> Path:
    return Path(os.path.expanduser(raw)).resolve()


def _discover_pdfs(input_dir: Path) -> list[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")


def _parse_json_text(raw: str) -> dict[str, Any] | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _load_report(sidecar: Path, stdout_text: str) -> tuple[dict[str, Any] | None, str]:
    if sidecar.exists():
        try:
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data, "sidecar"
        except Exception:
            pass
    parsed = _parse_json_text(stdout_text)
    if parsed is not None:
        return parsed, "stdout"
    return None, "missing"


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _status_counter(report: dict[str, Any] | None) -> dict[str, int]:
    counter = report.get("status_counter") if isinstance(report, dict) else {}
    if not isinstance(counter, dict):
        counter = {}
    return {
        "success": _as_int(counter.get("success", 0)),
        "partial": _as_int(counter.get("partial", 0)),
        "failed": _as_int(counter.get("failed", 0)),
    }


def _build_summary(status: str, message: str, **extra: Any) -> dict[str, Any]:
    summary = {
        "status": status,
        "message": message,
        "origin_id": REQUEST_PAYLOAD["origin_id"],
        "title": REQUEST_PAYLOAD["title"],
        "description": REQUEST_PAYLOAD["description"],
        "labels": REQUEST_PAYLOAD["labels"],
        "readonly_scope": {
            "external_writeback": False,
            "trello_writeback": False,
            "local_filesystem_writes_possible": True,
        },
    }
    summary.update(extra)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Readonly reviewable inbox runner for reviewed PDF-to-Excel delegate.")
    parser.add_argument("--input-dir", default="~/Desktop/pdf样本", help="Directory containing input PDFs.")
    parser.add_argument("--output-xlsx", default="artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx", help="Target XLSX output path.")
    parser.add_argument("--ocr", default="auto", choices=["auto", "on", "off"], help="OCR mode passed through to delegate.")
    parser.add_argument("--dry-run", action="store_true", help="Delegate dry-run mode; remains a reviewable partial outcome.")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Timeout for delegate subprocess execution.")
    args = parser.parse_args()

    repo_root = _repo_root()
    script_path = Path(__file__).resolve()
    delegate_path = (repo_root / "artifacts/scripts/pdf_to_excel_ocr.py").resolve()
    input_dir = _expand_path(args.input_dir)
    output_xlsx = _expand_path(args.output_xlsx) if os.path.isabs(os.path.expanduser(args.output_xlsx)) else (repo_root / args.output_xlsx).resolve()

    if output_xlsx.suffix.lower() != ".xlsx":
        print(json.dumps(_build_summary(
            "failed",
            "Refusing to run because output_xlsx must end with .xlsx for true workbook semantics.",
            runtime_summary={
                "script": str(script_path),
                "delegate": str(delegate_path),
                "input_dir": str(input_dir),
                "output_xlsx": str(output_xlsx),
                "ocr": args.ocr,
                "dry_run": args.dry_run,
                "timeout_seconds": args.timeout_seconds,
            },
        ), ensure_ascii=False, indent=2))
        return 2

    discovered_pdfs = _discover_pdfs(input_dir)
    preflight = {
        "input_dir": str(input_dir),
        "output_xlsx": str(output_xlsx),
        "ocr": args.ocr,
        "dry_run": args.dry_run,
        "timeout_seconds": args.timeout_seconds,
        "delegate_path": str(delegate_path),
        "discovered_pdf_count": len(discovered_pdfs),
        "discovered_pdfs_sample": [str(p) for p in discovered_pdfs[:20]],
        "readonly_semantics": "No external or Trello writeback. Local output files may be written when dry_run=false.",
    }

    if not delegate_path.exists():
        print(json.dumps(_build_summary(
            "failed",
            "Reviewed delegate script was not found; refusing to broaden behavior with an arbitrary helper.",
            runtime_summary=preflight,
            limitations=["Missing reviewed delegate artifacts/scripts/pdf_to_excel_ocr.py"],
            next_steps=["Restore the reviewed delegate script and rerun the wrapper."],
        ), ensure_ascii=False, indent=2))
        return 2

    with tempfile.TemporaryDirectory(prefix="pdf_to_excel_runner_") as tmpdir:
        report_path = Path(tmpdir) / "delegate_report.json"
        cmd = [
            sys.executable,
            str(delegate_path),
            "--input-dir", str(input_dir),
            "--output-xlsx", str(output_xlsx),
            "--ocr", args.ocr,
            "--report-json", str(report_path),
        ]
        if args.dry_run:
            cmd.append("--dry-run")

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=max(1, args.timeout_seconds),
                cwd=str(repo_root),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            print(json.dumps(_build_summary(
                "failed",
                "Delegate execution timed out.",
                runtime_summary={
                    **preflight,
                    "delegate_command": cmd,
                    "timeout_seconds": args.timeout_seconds,
                    "stdout_excerpt": (exc.stdout or "")[:4000],
                    "stderr_excerpt": (exc.stderr or "")[:4000],
                },
                limitations=["Delegate subprocess exceeded the configured timeout."],
                next_steps=["Inspect the input PDFs and delegate runtime dependencies.", "Retry with a larger --timeout-seconds value if appropriate."],
            ), ensure_ascii=False, indent=2))
            return 2

        report, report_source = _load_report(report_path, proc.stdout)
        delegate_status = report.get("status") if isinstance(report, dict) else None
        total_files = _as_int(report.get("total_files"), 0) if isinstance(report, dict) else 0
        delegate_dry_run = bool(report.get("dry_run")) if isinstance(report, dict) else args.dry_run
        counter = _status_counter(report)
        excel_written = bool(report.get("excel_written")) if isinstance(report, dict) else False
        output_exists = bool(report.get("output_exists")) if isinstance(report, dict) else output_xlsx.exists()
        output_size_bytes = _as_int(report.get("output_size_bytes"), 0) if isinstance(report, dict) else (output_xlsx.stat().st_size if output_xlsx.exists() else 0)
        ocr_runtime_status = report.get("ocr_runtime_status") if isinstance(report, dict) else None

        runtime_summary = {
            **preflight,
            "delegate_command": cmd,
            "delegate_exit_code": proc.returncode,
            "delegate_report_source": report_source,
            "delegate_status": delegate_status,
            "delegate_total_files": total_files,
            "delegate_dry_run": delegate_dry_run,
            "delegate_status_counter": counter,
            "excel_written": excel_written,
            "output_exists": output_exists,
            "output_size_bytes": output_size_bytes,
            "ocr_runtime_status": ocr_runtime_status,
            "stdout_excerpt": (proc.stdout or "")[:4000],
            "stderr_excerpt": (proc.stderr or "")[:4000],
        }

        success_gates = all([
            delegate_status == "success",
            total_files >= 1,
            delegate_dry_run is False,
            counter.get("failed", 0) == 0,
            counter.get("partial", 0) == 0,
            excel_written is True,
            output_exists is True,
            output_size_bytes > 0,
        ])

        if args.ocr in {"auto", "on"} and ocr_runtime_status in {"blocked", "partial"}:
            print(json.dumps(_build_summary(
                "partial",
                "Delegate reported limited OCR sufficiency; not claiming success.",
                runtime_summary=runtime_summary,
                limitations=["OCR runtime status was reported as blocked/partial."],
                next_steps=["Review OCR/runtime dependencies and inspect the generated evidence before rerunning."],
                delegate_report=report,
            ), ensure_ascii=False, indent=2))
            return 0

        if success_gates:
            print(json.dumps(_build_summary(
                "success",
                "Reviewed delegate reported a strong success outcome and attested a real XLSX output.",
                runtime_summary=runtime_summary,
                delegate_report=report,
            ), ensure_ascii=False, indent=2))
            return 0

        if delegate_status == "partial":
            limitations = []
            if delegate_dry_run:
                limitations.append("Dry-run was requested; no final XLSX success claim is appropriate.")
            if total_files == 0:
                limitations.append("No PDF inputs were discovered or processed.")
            if counter.get("partial", 0) > 0 or counter.get("failed", 0) > 0:
                limitations.append("Delegate reported partial/failed file-level outcomes.")
            if args.ocr in {"auto", "on"} and ocr_runtime_status:
                limitations.append(f"OCR runtime status: {ocr_runtime_status}.")
            if not limitations:
                limitations.append("Delegate provided a reviewable partial outcome.")
            print(json.dumps(_build_summary(
                "partial",
                "Best-effort delegate outcome remained partial; preserving that status with explicit limitations.",
                runtime_summary=runtime_summary,
                limitations=limitations,
                next_steps=[
                    "Inspect the delegate report and stdout/stderr excerpts.",
                    "Verify PDF inputs and OCR/runtime dependencies.",
                    "Rerun without --dry-run once the environment is ready for a real workbook write."
                ],
                delegate_report=report,
            ), ensure_ascii=False, indent=2))
            return 0

        if args.dry_run or len(discovered_pdfs) == 0:
            limitations = []
            if args.dry_run:
                limitations.append("Dry-run requests are reviewable-only and do not justify success.")
            if len(discovered_pdfs) == 0:
                limitations.append("Zero PDFs discovered during wrapper preflight.")
            if report is None:
                limitations.append("Delegate did not provide canonical structured evidence.")
            print(json.dumps(_build_summary(
                "partial",
                "Reviewable partial outcome due to dry-run and/or zero-PDF discovery.",
                runtime_summary=runtime_summary,
                limitations=limitations,
                next_steps=[
                    "Add or verify input PDFs under the provided input directory.",
                    "Run again without --dry-run when ready to produce a workbook."
                ],
                delegate_report=report,
            ), ensure_ascii=False, indent=2))
            return 0

        print(json.dumps(_build_summary(
            "failed",
            "Delegate did not provide strong enough evidence for success, and no contract-compliant partial outcome was established.",
            runtime_summary=runtime_summary,
            limitations=[
                "Wrapper does not treat exit code plus output-file existence alone as sufficient success evidence.",
                "Required delegate evidence gates were not all satisfied."
            ],
            next_steps=[
                "Inspect the delegate JSON report for missing attestation fields.",
                "Confirm the reviewed delegate supports --report-json and emits canonical status/total_files/status_counter/dry_run fields."
            ],
            delegate_report=report,
        ), ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
