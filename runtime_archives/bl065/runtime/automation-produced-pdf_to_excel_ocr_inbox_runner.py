#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_TIMEOUT_SECONDS = 1800


@dataclass
class WrapperContext:
    script_path: Path
    repo_root: Path
    delegate_path: Path


def _expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def _resolve_repo_root(script_path: Path) -> Path:
    # Expected location: <repo>/artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py
    return script_path.resolve().parents[2]


def _resolve_delegate(preferred_base_script: str, ctx: WrapperContext) -> Path:
    candidate = Path(preferred_base_script)
    if candidate.is_absolute():
        return candidate

    repo_candidate = (ctx.repo_root / candidate).resolve()
    if repo_candidate.exists():
        return repo_candidate

    script_dir_candidate = (ctx.script_path.resolve().parent / candidate).resolve()
    if script_dir_candidate.exists():
        return script_dir_candidate

    return repo_candidate


def _discover_pdfs(input_dir: Path) -> List[Path]:
    if not input_dir.exists() or not input_dir.is_dir():
        return []
    return sorted(p for p in input_dir.rglob("*.pdf") if p.is_file()) + sorted(
        p for p in input_dir.rglob("*.PDF") if p.is_file()
    )


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        if path.exists() and path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return None


def _parse_json_from_stdout(stdout: str) -> Optional[Dict[str, Any]]:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue
    return None


def _status_counter(report: Dict[str, Any]) -> Dict[str, int]:
    raw = report.get("status_counter")
    if isinstance(raw, dict):
        return {
            "success": _safe_int(raw.get("success", 0)),
            "partial": _safe_int(raw.get("partial", 0)),
            "failed": _safe_int(raw.get("failed", 0)),
        }
    return {"success": 0, "partial": 0, "failed": 0}


def _report_runtime_summary(
    *,
    status: str,
    params: Dict[str, Any],
    discovered_pdfs: List[Path],
    delegate_report: Optional[Dict[str, Any]],
    delegate_cmd: List[str],
    delegate_exit_code: Optional[int],
    timeout_seconds: int,
    limitations: List[str],
    next_steps: List[str],
    preflight_notes: List[str],
) -> Dict[str, Any]:
    return {
        "status": status,
        "origin_id": params.get("origin_id"),
        "title": params.get("title"),
        "description": params.get("description"),
        "labels": list(params.get("labels") or []),
        "readonly_semantics": {
            "external_writeback": False,
            "local_output_possible": not bool(params.get("dry_run", False)),
            "note": "Readonly means no external/Trello writeback is expected in this smoke step; local filesystem output may still occur when dry_run=false.",
        },
        "inputs": {
            "input_dir": params.get("input_dir"),
            "output_xlsx": params.get("output_xlsx"),
            "ocr": params.get("ocr"),
            "dry_run": bool(params.get("dry_run", False)),
        },
        "preflight": {
            "pdf_discovery_mode": "recursive",
            "discovered_pdf_count": len(discovered_pdfs),
            "discovered_pdf_samples": [str(p) for p in discovered_pdfs[:20]],
            "notes": preflight_notes,
        },
        "delegate": {
            "command": delegate_cmd,
            "shell_escaped": " ".join(shlex.quote(part) for part in delegate_cmd),
            "exit_code": delegate_exit_code,
            "timeout_seconds": timeout_seconds,
            "report": delegate_report,
        },
        "limitations": limitations,
        "next_steps": next_steps,
    }


def _evaluate_outcome(
    *,
    params: Dict[str, Any],
    discovered_pdfs: List[Path],
    delegate_report: Optional[Dict[str, Any]],
) -> (str, List[str], List[str]):
    limitations: List[str] = []
    next_steps: List[str] = []

    if not discovered_pdfs:
        limitations.append("No PDF files were discovered under input_dir using recursive discovery.")
        next_steps.append("Place one or more PDF files under the provided input_dir and rerun the wrapper.")
        return "partial", limitations, next_steps

    if delegate_report is None:
        limitations.append("No structured delegate report was available from sidecar JSON or stdout fallback.")
        next_steps.append("Inspect delegate logs and ensure the reviewed delegate supports --report-json and emits canonical JSON evidence.")
        return "failed", limitations, next_steps

    delegate_status = str(delegate_report.get("status") or "").strip().lower()
    total_files = _safe_int(delegate_report.get("total_files"), 0)
    dry_run = bool(delegate_report.get("dry_run", False))
    counter = _status_counter(delegate_report)
    excel_written = bool(delegate_report.get("excel_written", False))
    output_exists = bool(delegate_report.get("output_exists", False))
    output_size_bytes = _safe_int(delegate_report.get("output_size_bytes"), 0)
    ocr_mode = str(params.get("ocr") or "").strip().lower()
    ocr_runtime_status = str(delegate_report.get("ocr_runtime_status") or "").strip().lower()

    if delegate_status == "partial":
        limitations.append("Delegate reported partial outcome; wrapper preserves partial for best-effort readonly reviewability.")
        if ocr_mode in {"auto", "on"} and ocr_runtime_status in {"blocked", "partial"}:
            limitations.append(f"OCR sufficiency is limited: delegate reported ocr_runtime_status={ocr_runtime_status} while ocr={ocr_mode}.")
        next_steps.append("Review delegate report details to determine whether OCR/runtime dependencies or source PDF characteristics limited extraction.")
        next_steps.append("If acceptable, install/enable the missing OCR/runtime components and rerun for stronger evidence.")
        return "partial", limitations, next_steps

    if delegate_status == "failed":
        limitations.append("Delegate reported failed outcome.")
        next_steps.append("Inspect the delegate report and stderr output, then address the reported failure before rerunning.")
        return "failed", limitations, next_steps

    if delegate_status != "success":
        limitations.append(f"Delegate reported unsupported or empty status: {delegate_status or 'missing'}.")
        next_steps.append("Ensure the reviewed delegate emits canonical status values success/partial/failed.")
        return "failed", limitations, next_steps

    if dry_run:
        limitations.append("Dry-run execution was delegated and completed without claiming production workbook success.")
        next_steps.append("Rerun without --dry-run to attempt real XLSX output generation.")
        return "partial", limitations, next_steps

    if total_files < 1:
        limitations.append("Delegate success claim lacked evidence of at least one processed input file.")
        next_steps.append("Verify PDF discovery under the provided input_dir and rerun.")
        return "failed", limitations, next_steps

    if counter.get("failed", 0) != 0 or counter.get("partial", 0) != 0:
        limitations.append("Delegate reported mixed per-file outcomes; wrapper refuses full success under the success evidence gate.")
        next_steps.append("Resolve partial/failed file-level outcomes and rerun for a clean success attestation.")
        return "partial", limitations, next_steps

    if ocr_mode in {"auto", "on"} and ocr_runtime_status in {"blocked", "partial"}:
        limitations.append(f"OCR runtime sufficiency is incomplete: ocr={ocr_mode}, delegate reported ocr_runtime_status={ocr_runtime_status}.")
        next_steps.append("Enable a complete OCR runtime or rerun with compatible source PDFs to achieve stronger review evidence.")
        return "partial", limitations, next_steps

    if not (excel_written and output_exists and output_size_bytes > 0):
        limitations.append("Delegate success claim did not satisfy workbook attestation gates (excel_written/output_exists/output_size_bytes).")
        next_steps.append("Inspect delegate output generation and ensure a real XLSX workbook is written before claiming success.")
        return "failed", limitations, next_steps

    return "success", limitations, next_steps


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Best-effort reviewable inbox runner for reviewed PDF-to-Excel OCR delegate."
    )
    parser.add_argument("--input-dir", required=True, help="Input directory containing PDFs.")
    parser.add_argument("--output-xlsx", required=True, help="Target XLSX output path.")
    parser.add_argument("--ocr", default="auto", choices=["auto", "on", "off"], help="OCR mode to pass through.")
    parser.add_argument("--dry-run", action="store_true", help="Delegate dry-run to the reviewed script.")
    parser.add_argument("--origin-id", default="", help="Traceability origin identifier.")
    parser.add_argument("--title", default="", help="Traceability title.")
    parser.add_argument("--description", default="", help="Traceability description.")
    parser.add_argument("--labels", nargs="*", default=None, help="Optional traceability labels.")
    parser.add_argument(
        "--preferred-base-script",
        default="artifacts/scripts/pdf_to_excel_ocr.py",
        help="Preferred reviewed delegate script path, resolved relative to repository or script location.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Explicit delegate subprocess timeout in seconds.",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = _resolve_repo_root(script_path)
    ctx = WrapperContext(
        script_path=script_path,
        repo_root=repo_root,
        delegate_path=Path(),
    )
    delegate_path = _resolve_delegate(args.preferred_base_script, ctx)
    ctx.delegate_path = delegate_path

    params: Dict[str, Any] = {
        "input_dir": args.input_dir,
        "output_xlsx": args.output_xlsx,
        "ocr": args.ocr,
        "dry_run": bool(args.dry_run),
        "origin_id": args.origin_id,
        "title": args.title,
        "description": args.description,
        "labels": list(args.labels or []),
        "preferred_base_script": args.preferred_base_script,
    }

    input_dir = _expand_path(args.input_dir)
    output_xlsx = _expand_path(args.output_xlsx)
    preflight_notes: List[str] = []

    if output_xlsx.suffix.lower() != ".xlsx":
        runtime_summary = _report_runtime_summary(
            status="failed",
            params=params,
            discovered_pdfs=[],
            delegate_report=None,
            delegate_cmd=[],
            delegate_exit_code=None,
            timeout_seconds=args.timeout_seconds,
            limitations=["Requested output path does not end with .xlsx; refusing mismatched output semantics."],
            next_steps=["Provide an output_xlsx path ending in .xlsx and rerun."],
            preflight_notes=preflight_notes,
        )
        print(json.dumps(runtime_summary, ensure_ascii=False, indent=2))
        return 2

    if not delegate_path.exists() or not delegate_path.is_file():
        runtime_summary = _report_runtime_summary(
            status="failed",
            params=params,
            discovered_pdfs=[],
            delegate_report=None,
            delegate_cmd=[sys.executable, str(delegate_path)],
            delegate_exit_code=None,
            timeout_seconds=args.timeout_seconds,
            limitations=[f"Reviewed delegate script was not found: {delegate_path}"],
            next_steps=["Restore the reviewed delegate at artifacts/scripts/pdf_to_excel_ocr.py or pass a valid compatible path."],
            preflight_notes=preflight_notes,
        )
        print(json.dumps(runtime_summary, ensure_ascii=False, indent=2))
        return 2

    discovered_pdfs = _discover_pdfs(input_dir)
    preflight_notes.append("Recursive PDF discovery is used to keep wrapper evidence aligned with delegate-oriented inbox semantics.")

    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(prefix="pdf_to_excel_delegate_report_", suffix=".json", delete=False) as tmp:
        report_json_path = Path(tmp.name)

    delegate_cmd: List[str] = [
        sys.executable,
        str(delegate_path),
        "--input-dir",
        str(input_dir),
        "--output-xlsx",
        str(output_xlsx),
        "--ocr",
        args.ocr,
        "--report-json",
        str(report_json_path),
    ]
    if args.dry_run:
        delegate_cmd.append("--dry-run")

    delegate_exit_code: Optional[int] = None
    stdout_text = ""
    stderr_text = ""
    delegate_report: Optional[Dict[str, Any]] = None

    try:
        completed = subprocess.run(
            delegate_cmd,
            capture_output=True,
            text=True,
            timeout=args.timeout_seconds,
            cwd=str(repo_root),
            check=False,
        )
        delegate_exit_code = completed.returncode
        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""
        delegate_report = _load_json_file(report_json_path)
        if delegate_report is None:
            delegate_report = _parse_json_from_stdout(stdout_text)

        if delegate_report is None and delegate_exit_code != 0:
            runtime_summary = _report_runtime_summary(
                status="failed",
                params=params,
                discovered_pdfs=discovered_pdfs,
                delegate_report={
                    "stderr": stderr_text,
                    "stdout": stdout_text,
                },
                delegate_cmd=delegate_cmd,
                delegate_exit_code=delegate_exit_code,
                timeout_seconds=args.timeout_seconds,
                limitations=["Delegate exited non-zero and no canonical structured report was available."],
                next_steps=["Inspect stderr/stdout in the runtime summary and correct the delegate failure before rerunning."],
                preflight_notes=preflight_notes,
            )
            print(json.dumps(runtime_summary, ensure_ascii=False, indent=2))
            return 1

        status, limitations, next_steps = _evaluate_outcome(
            params=params,
            discovered_pdfs=discovered_pdfs,
            delegate_report=delegate_report,
        )

        if stderr_text.strip():
            limitations.append("Delegate emitted stderr output; inspect delegate.report or captured process logs if additional diagnostics are needed.")

        runtime_summary = _report_runtime_summary(
            status=status,
            params=params,
            discovered_pdfs=discovered_pdfs,
            delegate_report=delegate_report,
            delegate_cmd=delegate_cmd,
            delegate_exit_code=delegate_exit_code,
            timeout_seconds=args.timeout_seconds,
            limitations=limitations,
            next_steps=next_steps,
            preflight_notes=preflight_notes,
        )
        print(json.dumps(runtime_summary, ensure_ascii=False, indent=2))
        return 0 if status == "success" else 1 if status == "failed" else 3

    except subprocess.TimeoutExpired as exc:
        delegate_exit_code = None
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""
        delegate_report = _load_json_file(report_json_path)
        status = "partial" if args.dry_run or discovered_pdfs else "failed"
        limitations = [f"Delegate execution exceeded timeout of {args.timeout_seconds} seconds."]
        next_steps = ["Investigate long-running PDF/OCR processing, reduce workload, or increase timeout if justified."]
        runtime_summary = _report_runtime_summary(
            status=status,
            params=params,
            discovered_pdfs=discovered_pdfs,
            delegate_report=delegate_report or {"stdout": stdout_text, "stderr": stderr_text, "timeout": True},
            delegate_cmd=delegate_cmd,
            delegate_exit_code=delegate_exit_code,
            timeout_seconds=args.timeout_seconds,
            limitations=limitations,
            next_steps=next_steps,
            preflight_notes=preflight_notes,
        )
        print(json.dumps(runtime_summary, ensure_ascii=False, indent=2))
        return 1 if status == "failed" else 3
    finally:
        try:
            report_json_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
