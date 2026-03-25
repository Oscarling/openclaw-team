# Delegate OCR/Status Reporting Hardening Report

## Objective

Complete `BL-20260325-048` by hardening delegate OCR/status/reporting semantics
so best-effort readonly outcomes remain truthful and evidence-rich, addressing
critic findings surfaced in `BL-20260325-047`.

## Scope

In scope:

- refine delegate per-file status semantics when text exists but extraction
  attempts include errors
- enrich delegate JSON report with per-file evidence and actionable guidance
- add focused tests for delegate status/report contract behavior

Out of scope:

- live governed rerun in this phase
- runtime endpoint/retry policy changes
- Trello or finalization flow changes

## Changes

### 1) Hardened per-file status semantics for mixed extraction outcomes

Updated `artifacts/scripts/pdf_to_excel_ocr.py`:

- in `process_one_pdf(...)`, when text is extracted but OCR/extraction errors are
  present, status is now `partial` (with explicit warning) instead of always
  `success`
- this prevents over-claiming successful extraction in mixed-evidence paths and
  keeps outcomes aligned with best-effort honesty

### 2) Enriched delegate report contract for reviewability

Updated `artifacts/scripts/pdf_to_excel_ocr.py` report payload:

- added `files` with per-file structured evidence (`FileResult` fields)
- added `notes` and `next_steps` for actionable guidance
- preserved existing aggregate fields (`status`, `status_counter`,
  `total_files`, output attestation) for compatibility
- added `next_steps` on no-file path and write-failure path to improve
  downstream diagnosis quality

### 3) Added focused regression tests

Added `tests/test_pdf_to_excel_ocr_script.py`:

- verifies per-file status is `partial` when text exists but OCR step fails
- verifies clean extraction path remains `success`
- verifies `main()` report includes `files`, `notes`, and `next_steps` with
  partial evidence guidance

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_script.py`
- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-048` can be treated as complete as a source-side blocker-hardening
phase.

Delegate outcomes and reporting are now more evidence-rich and semantically
conservative for best-effort readonly flows.

Next required step: run a fresh same-origin governed validation to verify
whether critic findings on delegate OCR/status/reporting evidence quality are
reduced under real execute.
