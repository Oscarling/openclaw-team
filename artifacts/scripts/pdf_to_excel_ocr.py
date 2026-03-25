#!/usr/bin/env python3
"""
Batch PDF -> Excel extractor with optional OCR fallback.

Design goals:
- Batch processing with per-file isolation (single file failure must not stop the batch)
- OCR mode: auto | on | off
- Chinese-friendly OCR defaults (chi_sim+eng)
- Dry-run support for pilot validation when dependencies are unavailable
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


try:
    from pypdf import PdfReader  # type: ignore
except Exception:
    PdfReader = None

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None

try:
    import pytesseract  # type: ignore
except Exception:
    pytesseract = None

try:
    from pdf2image import convert_from_path  # type: ignore
except Exception:
    convert_from_path = None


@dataclass
class FileResult:
    file_name: str
    file_path: str
    status: str
    extract_method: str
    page_count: int
    text_chars: int
    text_preview: str
    warnings: str
    error: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch PDF to Excel extractor with OCR fallback.")
    parser.add_argument("--input-dir", required=True, help="Directory containing PDF files.")
    parser.add_argument("--output-xlsx", required=True, help="Output Excel path.")
    parser.add_argument(
        "--ocr",
        choices=("auto", "on", "off"),
        default="auto",
        help="OCR mode. auto=use OCR when plain text extraction is weak.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write Excel file. Print execution summary only.",
    )
    parser.add_argument(
        "--ocr-lang",
        default="chi_sim+eng",
        help="OCR language pack for pytesseract, default supports Chinese + English.",
    )
    parser.add_argument(
        "--auto-ocr-min-chars",
        type=int,
        default=50,
        help="In auto mode, run OCR when extracted text chars < this threshold.",
    )
    parser.add_argument(
        "--report-json",
        default="",
        help="Optional sidecar path for writing the same JSON report emitted to stdout.",
    )
    return parser.parse_args()


def discover_pdfs(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
    files = sorted([p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"])
    return files


def detect_ocr_runtime_status() -> tuple[str, list[str]]:
    missing: list[str] = []
    present: list[str] = []

    if pytesseract is None:
        missing.append("python module pytesseract")
    else:
        present.append("python module pytesseract")
    if convert_from_path is None:
        missing.append("python module pdf2image")
    else:
        present.append("python module pdf2image")
    if shutil.which("tesseract") is None:
        missing.append("binary tesseract")
    else:
        present.append("binary tesseract")
    if shutil.which("pdftoppm") is None:
        missing.append("binary pdftoppm (poppler)")
    else:
        present.append("binary pdftoppm (poppler)")

    if not missing:
        return "available", []
    if present:
        return "partial", missing
    return "blocked", missing


def extract_text_pypdf(pdf_path: Path) -> tuple[str, int]:
    if PdfReader is None:
        raise RuntimeError("pypdf not installed")
    reader = PdfReader(str(pdf_path))
    page_texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        page_texts.append(text)
    return "\n".join(page_texts), len(reader.pages)


def extract_text_ocr(pdf_path: Path, ocr_lang: str) -> str:
    if pytesseract is None:
        raise RuntimeError("pytesseract not installed")
    if convert_from_path is None:
        raise RuntimeError("pdf2image not installed")
    if shutil.which("tesseract") is None:
        raise RuntimeError("tesseract binary not found")
    if shutil.which("pdftoppm") is None:
        raise RuntimeError("pdftoppm binary not found (install poppler)")

    images = convert_from_path(str(pdf_path), dpi=220)
    chunks: list[str] = []
    for image in images:
        chunks.append(pytesseract.image_to_string(image, lang=ocr_lang))
    return "\n".join(chunks)


def compact_preview(text: str, limit: int = 160) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= limit:
        return single_line
    return single_line[: limit - 3] + "..."


def process_one_pdf(
    pdf_path: Path,
    ocr_mode: str,
    ocr_lang: str,
    auto_ocr_min_chars: int,
) -> FileResult:
    warnings: list[str] = []
    errors: list[str] = []
    method = "none"
    text = ""
    page_count = 0

    try:
        text, page_count = extract_text_pypdf(pdf_path)
        method = "text"
    except Exception as e:
        warnings.append(f"text extraction unavailable: {e}")

    needs_ocr = False
    if ocr_mode == "on":
        needs_ocr = True
    elif ocr_mode == "auto" and len(text.strip()) < auto_ocr_min_chars:
        needs_ocr = True

    if needs_ocr:
        try:
            ocr_text = extract_text_ocr(pdf_path, ocr_lang).strip()
            if ocr_text:
                if text.strip():
                    text = f"{text.strip()}\n\n[OCR Fallback]\n{ocr_text}"
                    method = "text+ocr"
                else:
                    text = ocr_text
                    method = "ocr"
            else:
                warnings.append("OCR returned empty text")
        except Exception as e:
            errors.append(f"OCR failed: {e}")

    if not text.strip():
        if errors:
            status = "failed"
        else:
            status = "partial"
            warnings.append("No extractable text captured")
    else:
        status = "success"

    return FileResult(
        file_name=pdf_path.name,
        file_path=str(pdf_path),
        status=status,
        extract_method=method,
        page_count=page_count,
        text_chars=len(text),
        text_preview=compact_preview(text),
        warnings=" | ".join(warnings),
        error=" | ".join(errors),
    )


def write_excel(results: list[FileResult], output_xlsx: Path) -> None:
    if pd is None:
        raise RuntimeError("pandas is required to write Excel output")
    output_xlsx.parent.mkdir(parents=True, exist_ok=True)

    rows = [asdict(r) for r in results]
    detail_df = pd.DataFrame(rows)

    summary_rows: list[dict[str, Any]] = []
    by_status = detail_df.groupby("status").size().to_dict()
    by_method = detail_df.groupby("extract_method").size().to_dict()
    for key, value in sorted(by_status.items()):
        summary_rows.append({"metric": "status_count", "name": key, "value": int(value)})
    for key, value in sorted(by_method.items()):
        summary_rows.append({"metric": "method_count", "name": key, "value": int(value)})
    summary_rows.append({"metric": "total_files", "name": "all", "value": int(len(results))})
    summary_df = pd.DataFrame(summary_rows)

    with pd.ExcelWriter(output_xlsx) as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        detail_df.to_excel(writer, sheet_name="files", index=False)


def emit_report(report: dict[str, Any], report_json: str) -> None:
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if not report_json:
        return
    out_path = Path(report_json).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_xlsx = Path(args.output_xlsx).expanduser().resolve()

    try:
        pdf_files = discover_pdfs(input_dir)
    except Exception as e:
        emit_report({"status": "failed", "error": str(e)}, args.report_json)
        return 2

    if not pdf_files:
        emit_report(
            {
                "status": "partial",
                "input_dir": str(input_dir),
                "output_xlsx": str(output_xlsx),
                "ocr_mode": args.ocr,
                "total_files": 0,
                "status_counter": {},
                "dry_run": bool(args.dry_run),
                "excel_written": False,
                "output_exists": False,
                "output_size_bytes": 0,
                "notes": [f"No PDF files found under {input_dir}"],
            },
            args.report_json,
        )
        return 0

    ocr_runtime, missing = detect_ocr_runtime_status()
    results: list[FileResult] = []
    for pdf in pdf_files:
        try:
            results.append(
                process_one_pdf(
                    pdf,
                    ocr_mode=args.ocr,
                    ocr_lang=args.ocr_lang,
                    auto_ocr_min_chars=args.auto_ocr_min_chars,
                )
            )
        except Exception as e:
            results.append(
                FileResult(
                    file_name=pdf.name,
                    file_path=str(pdf),
                    status="failed",
                    extract_method="none",
                    page_count=0,
                    text_chars=0,
                    text_preview="",
                    warnings="",
                    error=f"Unhandled processing exception: {e}",
                )
            )

    status_counter: dict[str, int] = {}
    for item in results:
        status_counter[item.status] = status_counter.get(item.status, 0) + 1

    failed_count = status_counter.get("failed", 0)
    partial_count = status_counter.get("partial", 0)
    if failed_count == 0 and partial_count == 0:
        aggregate_status = "success"
    else:
        aggregate_status = "partial"

    report = {
        "status": aggregate_status,
        "input_dir": str(input_dir),
        "output_xlsx": str(output_xlsx),
        "ocr_mode": args.ocr,
        "ocr_runtime_status": ocr_runtime,
        "ocr_missing_dependencies": missing,
        "total_files": len(results),
        "status_counter": status_counter,
        "dry_run": bool(args.dry_run),
        "excel_written": False,
        "output_exists": False,
        "output_size_bytes": 0,
    }

    if args.dry_run:
        emit_report(report, args.report_json)
        return 0

    try:
        write_excel(results, output_xlsx)
        report["output_exists"] = output_xlsx.exists() and output_xlsx.is_file()
        if report["output_exists"]:
            report["output_size_bytes"] = int(output_xlsx.stat().st_size)
        report["excel_written"] = bool(report["output_exists"] and report["output_size_bytes"] > 0)
        emit_report(report, args.report_json)
        return 0
    except Exception as e:
        report["status"] = "failed"
        report["error"] = str(e)
        report["output_exists"] = output_xlsx.exists() and output_xlsx.is_file()
        if report["output_exists"]:
            report["output_size_bytes"] = int(output_xlsx.stat().st_size)
        report["excel_written"] = bool(report["output_exists"] and report["output_size_bytes"] > 0)
        emit_report(report, args.report_json)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
