#!/usr/bin/env python3
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import xml.sax.saxutils as saxutils
import zipfile
from pathlib import Path

INPUT_DIR = os.path.expanduser("~/Desktop/pdf样本")
OUTPUT_XLSX = "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx"
OCR_MODE = "auto"
DRY_RUN = False
ORIGIN_ID = "trello:69c24cd3c1a2359ddd7a1bf8"
TITLE = "BL-20260324-014 live preview smoke sample 2026-03-24 (best-effort reviewable attempt)"
DESCRIPTION = "Purpose:"
LABELS = ["best_effort", "evidence_backed", "readonly", "reviewable", "trello"]


def xml_escape(value):
    return saxutils.escape(str(value), {'"': '&quot;'})


def run_capture(cmd):
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        return proc.returncode, proc.stdout, proc.stderr
    except Exception as exc:
        return 1, "", f"exception: {exc}"


def detect_tools():
    names = [
        "pdftotext",
        "pdfinfo",
        "pdftoppm",
        "tesseract",
    ]
    return {name: shutil.which(name) for name in names}


def list_pdfs(input_dir):
    root = Path(input_dir)
    if not root.exists() or not root.is_dir():
        return []
    return sorted([p for p in root.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"], key=lambda p: p.name.lower())


def get_pdfinfo(pdf_path, tools):
    info = {"pages": "", "title": "", "author": "", "producer": "", "raw": ""}
    if not tools.get("pdfinfo"):
        return info
    code, out, err = run_capture([tools["pdfinfo"], str(pdf_path)])
    raw = (out or "") + ("\n" + err if err else "")
    info["raw"] = raw.strip()
    if code != 0:
        return info
    for line in out.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        key = k.strip().lower()
        val = v.strip()
        if key == "pages":
            info["pages"] = val
        elif key == "title":
            info["title"] = val
        elif key == "author":
            info["author"] = val
        elif key == "producer":
            info["producer"] = val
    return info


def extract_with_pdftotext(pdf_path, tools):
    if not tools.get("pdftotext"):
        return False, "", "pdftotext not available"
    with tempfile.TemporaryDirectory() as tmpdir:
        out_txt = Path(tmpdir) / "out.txt"
        code, out, err = run_capture([tools["pdftotext"], "-layout", str(pdf_path), str(out_txt)])
        text = ""
        if out_txt.exists():
            try:
                text = out_txt.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = out_txt.read_text(errors="replace")
        if code == 0 and text.strip():
            return True, text, "pdftotext -layout"
        return False, text, (err or out or "pdftotext produced no usable text").strip()


def extract_with_ocr(pdf_path, tools):
    if not tools.get("pdftoppm") or not tools.get("tesseract"):
        return False, "", "OCR tools not fully available (need pdftoppm and tesseract)"
    combined = []
    details = []
    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = str(Path(tmpdir) / "page")
        code, out, err = run_capture([tools["pdftoppm"], "-r", "150", "-png", str(pdf_path), prefix])
        if code != 0:
            return False, "", (err or out or "pdftoppm failed").strip()
        images = sorted(Path(tmpdir).glob("page-*.png"))
        if not images:
            return False, "", "pdftoppm created no images"
        for img in images:
            base = img.with_suffix("")
            code, out, err = run_capture([tools["tesseract"], str(img), str(base), "txt"])
            txt_path = Path(str(base) + ".txt")
            page_text = ""
            if txt_path.exists():
                try:
                    page_text = txt_path.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    page_text = txt_path.read_text(errors="replace")
            details.append(f"{img.name}: rc={code}")
            if page_text.strip():
                combined.append(f"===== {img.name} =====\n{page_text}")
        final = "\n\n".join(combined).strip()
        if final:
            return True, final, "ocr via pdftoppm+tesseract"
        return False, "", "; ".join(details) if details else "OCR yielded no text"


def summarize_text(text, limit=2000):
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "\n...[truncated]"


def make_rows(pdfs, tools):
    rows = []
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    for pdf in pdfs:
        info = get_pdfinfo(pdf, tools)
        method = "none"
        status = "no_text"
        text = ""
        notes = []

        ok, extracted, detail = extract_with_pdftotext(pdf, tools)
        if ok:
            method = "pdftotext"
            status = "text_extracted"
            text = extracted
            notes.append(detail)
        else:
            notes.append(detail)
            if OCR_MODE in ("auto", "on"):
                ok2, extracted2, detail2 = extract_with_ocr(pdf, tools)
                notes.append(detail2)
                if ok2:
                    method = "ocr"
                    status = "ocr_text_extracted"
                    text = extracted2
                else:
                    status = "review_needed"

        row = {
            "origin_id": ORIGIN_ID,
            "title": TITLE,
            "labels": ",".join(LABELS),
            "generated_at_utc": now,
            "input_dir": str(Path(INPUT_DIR)),
            "pdf_file": pdf.name,
            "pdf_path": str(pdf),
            "pdf_size_bytes": str(pdf.stat().st_size),
            "pdf_pages": info.get("pages", ""),
            "pdf_title": info.get("title", ""),
            "pdf_author": info.get("author", ""),
            "pdf_producer": info.get("producer", ""),
            "extraction_status": status,
            "extraction_method": method,
            "ocr_mode": OCR_MODE,
            "tool_pdftotext": tools.get("pdftotext") or "",
            "tool_pdfinfo": tools.get("pdfinfo") or "",
            "tool_pdftoppm": tools.get("pdftoppm") or "",
            "tool_tesseract": tools.get("tesseract") or "",
            "notes": " | ".join(n for n in notes if n),
            "text_preview": summarize_text(text, limit=4000),
        }
        rows.append(row)
    return rows


def write_spreadsheetml(output_path, rows):
    headers = [
        "origin_id",
        "title",
        "labels",
        "generated_at_utc",
        "input_dir",
        "pdf_file",
        "pdf_path",
        "pdf_size_bytes",
        "pdf_pages",
        "pdf_title",
        "pdf_author",
        "pdf_producer",
        "extraction_status",
        "extraction_method",
        "ocr_mode",
        "tool_pdftotext",
        "tool_pdfinfo",
        "tool_pdftoppm",
        "tool_tesseract",
        "notes",
        "text_preview",
    ]

    lines = []
    lines.append('<?xml version="1.0"?>')
    lines.append('<?mso-application progid="Excel.Sheet"?>')
    lines.append('<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"')
    lines.append(' xmlns:o="urn:schemas-microsoft-com:office:office"')
    lines.append(' xmlns:x="urn:schemas-microsoft-com:office:excel"')
    lines.append(' xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"')
    lines.append(' xmlns:html="http://www.w3.org/TR/REC-html40">')
    lines.append(' <DocumentProperties xmlns="urn:schemas-microsoft-com:office:office">')
    lines.append(f'  <Author>{xml_escape("automation")}</Author>')
    lines.append(f'  <Title>{xml_escape(TITLE)}</Title>')
    lines.append(' </DocumentProperties>')
    lines.append(' <Worksheet ss:Name="pdf_extract">')
    lines.append('  <Table>')
    lines.append('   <Row>')
    for h in headers:
        lines.append(f'    <Cell><Data ss:Type="String">{xml_escape(h)}</Data></Cell>')
    lines.append('   </Row>')
    for row in rows:
        lines.append('   <Row>')
        for h in headers:
            value = row.get(h, "")
            lines.append(f'    <Cell><Data ss:Type="String">{xml_escape(value)}</Data></Cell>')
        lines.append('   </Row>')
    lines.append('  </Table>')
    lines.append(' </Worksheet>')
    lines.append('</Workbook>')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def main():
    print(f"[info] title: {TITLE}")
    print(f"[info] origin_id: {ORIGIN_ID}")
    print(f"[info] input_dir: {INPUT_DIR}")
    print(f"[info] output_xlsx: {OUTPUT_XLSX}")
    print(f"[info] dry_run: {DRY_RUN}")

    tools = detect_tools()
    print("[info] detected tools:")
    for name, path in tools.items():
        print(f"  - {name}: {path or 'not found'}")

    pdfs = list_pdfs(INPUT_DIR)
    print(f"[info] found {len(pdfs)} pdf(s)")
    for pdf in pdfs:
        print(f"  - {pdf}")

    if DRY_RUN:
        print("[info] dry_run enabled; no output written")
        return 0

    rows = make_rows(pdfs, tools)
    write_spreadsheetml(OUTPUT_XLSX, rows)
    print(f"[info] wrote reviewable workbook data to {OUTPUT_XLSX}")
    if not pdfs:
        print("[warn] no PDFs found; output contains headers only")
    unresolved = [r for r in rows if r.get("extraction_status") in ("review_needed", "no_text")]
    if unresolved:
        print(f"[warn] {len(unresolved)} file(s) need review or had no text extracted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
