# Critic Review: `pdf_to_excel_ocr.py`

## Review Scope
- Script: `artifacts/scripts/pdf_to_excel_ocr.py`
- Pilot input: `~/Desktop/pdf样本` (5 PDFs)
- Review date: 2026-03-19

## What Is Good
- Meets required CLI surface:
  - `--input-dir`
  - `--output-xlsx`
  - `--ocr auto|on|off`
  - `--dry-run`
- Batch behavior is isolation-safe: one file failure does not crash whole batch.
- OCR behavior is explicit and honest:
  - Detects missing OCR deps (`pytesseract`, `pdf2image`, `tesseract`, `pdftoppm`)
  - Returns blocker details instead of pretending OCR succeeded.
- Chinese compatibility intent is present (`--ocr-lang` default `chi_sim+eng`).

## Findings
- `P0` Environment blocker for real Excel output:
  - Current runtime misses `pandas`; non-dry-run exits with:
    - `pandas is required to write Excel output`
- `P1` Text extraction dependency missing in current runtime:
  - `pypdf` not installed, so native text extraction cannot run.
  - In `ocr=auto`, this causes all files to fall into OCR path, then fail because OCR stack is absent.

## Validation Evidence
- Dry-run command completed and returned structured status summary.
- Real run command failed transparently with dependency blocker.
- No false-positive "success" observed.

## Conclusion
- **Result: Conditional pass (logic pass, environment blocked).**
- The script itself is aligned with Phase 7 pilot goals, but the host environment is not yet ready for true PDF->Excel production output.
