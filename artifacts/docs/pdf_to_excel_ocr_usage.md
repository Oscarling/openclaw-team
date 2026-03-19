# PDF to Excel OCR Usage (Phase 7)

## Script
- `artifacts/scripts/pdf_to_excel_ocr.py`

## Input Directory
- Real pilot sample: `~/Desktop/pdf样本`

## Typical Commands
Dry-run:
```bash
python3 artifacts/scripts/pdf_to_excel_ocr.py \
  --input-dir ~/Desktop/pdf样本 \
  --output-xlsx /tmp/phase7_ocr_dryrun.xlsx \
  --ocr auto \
  --dry-run
```

Real output:
```bash
python3 artifacts/scripts/pdf_to_excel_ocr.py \
  --input-dir ~/Desktop/pdf样本 \
  --output-xlsx /tmp/phase7_ocr_real.xlsx \
  --ocr auto
```

## Arguments
- `--input-dir`: PDF root directory, supports batch traversal.
- `--output-xlsx`: output workbook path.
- `--ocr auto|on|off`:
  - `auto`: try text extraction first, fallback to OCR when text is weak.
  - `on`: force OCR path.
  - `off`: do not invoke OCR.
- `--dry-run`: no Excel file write, prints summary only.

## OCR Dependency Prerequisites
- Python packages:
  - `pandas`
  - `openpyxl`
  - `pypdf`
  - `pytesseract`
  - `pdf2image`
- System binaries:
  - `tesseract`
  - `pdftoppm` (from poppler)

## Common Troubleshooting
- Error: `pandas is required to write Excel output`
  - Install/repair: `python3 -m pip install --user pandas openpyxl`
- Error contains `tesseract binary not found`
  - Install `tesseract` and ensure it is in `PATH`.
- Error contains `pdftoppm binary not found`
  - Install poppler and ensure `pdftoppm` is in `PATH`.
- Many files return failed in `--ocr auto`
  - Run `bash artifacts/scripts/check_ocr_env.sh` and fix missing dependencies first.
