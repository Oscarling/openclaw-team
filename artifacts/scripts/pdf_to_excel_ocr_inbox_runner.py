#!/usr/bin/env python3
"""
Best-effort local PDF inventory manifest generator.

Purpose:
- Scan a local input directory for PDF files.
- Produce a deterministic, reviewable manifest at the requested output path.
- Avoid unsupported OCR or extraction claims.
- Remain runnable with standard library only; optionally writes true XLSX if
  openpyxl is available locally.

Configured from task parameters:
- input_dir: ~/Desktop/pdf样本
- output_xlsx: artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx
- ocr: auto (recorded as metadata only; no unsupported OCR is performed)
- dry_run: false
- origin_id: trello:69c1229edc9b8ec895640c5b
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

INPUT_DIR_RAW = "~/Desktop/pdf样本"
OUTPUT_XLSX_RAW = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
OCR_MODE = "auto"
DRY_RUN = False
ORIGIN_ID = "trello:69c1229edc9b8ec895640c5b"
TITLE = "Generate one local PDF inventory manifest script (best-effort reviewable attempt)"
DESCRIPTION = (
    "Use ~/Desktop/pdf样本 as input. Create one runnable local Python script that scans "
    "PDF files and writes one deterministic reviewable manifest under artifacts/. "
    "Local-only. Do not overclaim OCR/extraction behavior."
)
LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]

MANIFEST_COLUMNS = [
    "source_origin_id",
    "input_dir",
    "relative_path",
    "file_name",
    "file_size_bytes",
    "modified_time_utc",
    "sha256_first_1mb",
    "pdf_header",
    "is_probably_pdf",
    "ocr_mode_requested",
    "text_extraction_performed",
    "ocr_performed",
    "review_status",
    "notes",
]


def expand_path(raw: str) -> Path:
    return Path(os.path.expanduser(raw)).resolve()


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def sha256_first_1mb(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        hasher.update(fh.read(1024 * 1024))
    return hasher.hexdigest()


def read_pdf_header(path: Path) -> str:
    try:
        with path.open("rb") as fh:
            data = fh.read(8)
        if not data:
            return ""
        return data.decode("latin-1", errors="replace")
    except Exception as exc:
        return f"ERROR:{type(exc).__name__}"


def is_probably_pdf_from_header(header: str) -> bool:
    return header.startswith("%PDF-")


def iso_mtime_utc(path: Path) -> str:
    from datetime import datetime, timezone

    ts = path.stat().st_mtime
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iter_pdfs(root: Path) -> Iterable[Path]:
    if not root.exists() or not root.is_dir():
        return []
    return sorted(
        [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"],
        key=lambda p: str(p.relative_to(root)).replace("\\", "/"),
    )


def build_rows(input_dir: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for pdf_path in iter_pdfs(input_dir):
        rel = str(pdf_path.relative_to(input_dir)).replace("\\", "/")
        header = read_pdf_header(pdf_path)
        row = {
            "source_origin_id": ORIGIN_ID,
            "input_dir": str(input_dir),
            "relative_path": rel,
            "file_name": pdf_path.name,
            "file_size_bytes": str(pdf_path.stat().st_size),
            "modified_time_utc": iso_mtime_utc(pdf_path),
            "sha256_first_1mb": sha256_first_1mb(pdf_path),
            "pdf_header": header,
            "is_probably_pdf": "true" if is_probably_pdf_from_header(header) else "false",
            "ocr_mode_requested": OCR_MODE,
            "text_extraction_performed": "false",
            "ocr_performed": "false",
            "review_status": "inventory_only",
            "notes": "Deterministic manifest only; no OCR or text extraction attempted.",
        }
        rows.append(row)
    return rows


def write_xlsx_with_openpyxl(output_path: Path, rows: List[Dict[str, str]]) -> Tuple[bool, str]:
    try:
        from openpyxl import Workbook  # type: ignore
    except Exception as exc:
        return False, f"openpyxl unavailable: {type(exc).__name__}: {exc}"

    wb = Workbook()
    ws = wb.active
    ws.title = "pdf_manifest"
    ws.append(MANIFEST_COLUMNS)
    for row in rows:
        ws.append([row.get(col, "") for col in MANIFEST_COLUMNS])

    meta = wb.create_sheet("run_metadata")
    metadata_rows = [
        ("title", TITLE),
        ("description", DESCRIPTION),
        ("origin_id", ORIGIN_ID),
        ("ocr_mode_requested", OCR_MODE),
        ("dry_run", str(DRY_RUN).lower()),
        ("input_dir", str(expand_path(INPUT_DIR_RAW))),
        ("output_path", str(output_path)),
        ("row_count", str(len(rows))),
        ("writer", "openpyxl"),
        ("limitations", "No OCR or text extraction performed by this script."),
    ]
    for item in metadata_rows:
        meta.append(list(item))

    wb.save(output_path)
    return True, "wrote xlsx via openpyxl"


def write_csv_fallback(output_path: Path, rows: List[Dict[str, str]]) -> str:
    with output_path.open("w", encoding="utf-8", newline="") as fh:
        fh.write("# REVIEWABLE FALLBACK: CSV content stored at requested .xlsx path because openpyxl is unavailable.\n")
        fh.write("# This is not a true XLSX binary workbook. Rename to .csv if needed for import.\n")
        fh.write(f"# origin_id={ORIGIN_ID}\n")
        fh.write(f"# ocr_mode_requested={OCR_MODE}\n")
        fh.write("# text_extraction_performed=false\n")
        fh.write("# ocr_performed=false\n")
        writer = csv.DictWriter(fh, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return "wrote csv fallback at requested output path"


def main() -> int:
    input_dir = expand_path(INPUT_DIR_RAW)
    output_path = expand_path(OUTPUT_XLSX_RAW)
    ensure_parent_dir(output_path)

    rows = build_rows(input_dir)

    run_summary = {
        "title": TITLE,
        "origin_id": ORIGIN_ID,
        "input_dir": str(input_dir),
        "output_path": str(output_path),
        "ocr_mode_requested": OCR_MODE,
        "dry_run": DRY_RUN,
        "pdf_count": len(rows),
        "limitations": [
            "No OCR performed.",
            "No text extraction performed.",
            "Manifest reflects file inventory only.",
        ],
    }

    print(json.dumps(run_summary, ensure_ascii=False, indent=2))

    if DRY_RUN:
        return 0

    wrote_xlsx, detail = write_xlsx_with_openpyxl(output_path, rows)
    if not wrote_xlsx:
        detail = write_csv_fallback(output_path, rows) + f"; xlsx_unavailable_reason={detail}"

    print(detail)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
