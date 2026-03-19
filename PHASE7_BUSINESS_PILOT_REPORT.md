# Phase 7 Business Pilot Report

## Pilot Goal
Build a minimal business closed loop on real input directory `~/Desktop/pdf样本`:
- Automation generates batch PDF->Excel script with OCR fallback
- Critic reviews script and validation output
- Produce explicit pilot status and next-step recommendations

## Input Samples Used
Based on `PHASE7_INPUT_MANIFEST.md`, this pilot used 5 representative PDFs:
- Chinese educational content (`单词.pdf`)
- Invoice/form (`发票.pdf`)
- Official notice (`春季社会实践通知函.pdf`)
- Multi-page report (`服务报告2.pdf`)
- OCR-processed technical guide (`科学注塑实战指南_ocred.pdf`)

## Generated Files
- `PHASE7_INPUT_MANIFEST.md`
- `artifacts/scripts/pdf_to_excel_ocr.py`
- `artifacts/reviews/pdf_to_excel_ocr_review.md`
- `PHASE7_BUSINESS_PILOT_REPORT.md`

## Validation Commands and Results
1. Dry-run validation (real sample directory)
```bash
python3 artifacts/scripts/pdf_to_excel_ocr.py \
  --input-dir ~/Desktop/pdf样本 \
  --output-xlsx /tmp/phase7_pdf_to_excel.xlsx \
  --ocr auto \
  --dry-run
```
Result summary:
- `status`: `partial`
- `total_files`: `5`
- `status_counter`: `{"failed": 5}`
- `ocr_runtime_status`: `blocked`
- Missing OCR deps:
  - `python module pytesseract`
  - `python module pdf2image`
  - `binary tesseract`
  - `binary pdftoppm (poppler)`

2. Real write attempt (no dry-run)
```bash
python3 artifacts/scripts/pdf_to_excel_ocr.py \
  --input-dir ~/Desktop/pdf样本 \
  --output-xlsx /tmp/phase7_pdf_to_excel.xlsx \
  --ocr off
```
Result summary:
- `status`: `failed`
- blocker: `pandas is required to write Excel output`

## OCR Current Status
- **blocked**
- Reason: OCR runtime stack is absent in current host environment.

## Risk Assessment
- Immediate functional risk:
  - Cannot deliver real Excel output without `pandas`.
- OCR quality and coverage risk:
  - OCR path cannot execute until both Python modules and binaries are installed.
- Pilot interpretability risk:
  - Without `pypdf`, even text-based PDFs cannot be extracted in current runtime.

## Recommended Next Steps
1. Install minimal extraction/write dependencies:
   - `pypdf`
   - `pandas`
   - `openpyxl`
2. Install OCR stack:
   - `pytesseract`
   - `pdf2image`
   - `tesseract` binary
   - `poppler` (`pdftoppm`)
3. Re-run:
   - one dry-run with `--ocr auto`
   - one real run outputting to `artifacts/` with spot-check of produced workbook
4. Add one acceptance test fixture for:
   - text PDF path
   - OCR fallback path
   - single-file failure isolation
