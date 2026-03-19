# Phase 7.1 OCR Environment Setup Plan

## Purpose
Repair Phase 7 pilot blockers for PDF->Excel with OCR fallback, without modifying Phase 6 core runtime.

## Verified Baseline (Before Repair)
- Missing Python packages:
  - `pandas`
  - `pytesseract`
  - `pdf2image`
- Additional practical Python blockers for current script:
  - `pypdf` (native PDF text extraction)
  - `openpyxl` (Excel writer backend for pandas)
- Missing system binaries:
  - `tesseract`
  - `pdftoppm` (from poppler)

## Deliverables
- Env check script: `artifacts/scripts/check_ocr_env.sh`
- Conservative installer: `artifacts/scripts/install_ocr_env.sh`

## Conservative Repair Policy
- Allowed for auto-execution:
  - user-space Python package install via `python3 -m pip install --user ...`
- Not auto-executed in this task:
  - `brew install ...`
  - `sudo ...`
  - any irreversible system-level change

## Manual Commands (Operator Run)
Run these manually when you are ready:

```bash
brew update
brew install tesseract poppler
```

Optional Chinese OCR language data (if not included in your tesseract build):

```bash
brew install tesseract-lang
```

## Validation Plan
1. Run `check_ocr_env.sh`
2. Run `install_ocr_env.sh` (conservative only)
3. Re-run `check_ocr_env.sh`
4. Re-run pilot script on real input dir:
   - dry-run always
   - real output only if environment is sufficiently ready
