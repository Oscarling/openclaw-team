# Semantic Contract Alignment Hardening Report

## Objective

Complete `BL-20260325-036` by resolving the semantic contract mismatches
identified in `BL-20260325-035` between:

- wrapper success/partial semantics
- delegate aggregate status semantics
- delegate canonical output-write evidence fields

## Scope

In scope:

- delegate zero-input semantics hardening
- delegate aggregate status truthfulness hardening
- delegate output-write evidence enrichment
- wrapper success-evidence gate tightening to consume enriched delegate evidence
- focused regression coverage

Out of scope:

- fresh governed live Trello validation run
- prompt-policy redesign for automation/critic
- git finalization / Trello Done writeback

## Changes

### 1) Delegate zero-input semantics aligned to reviewable partial

Updated `artifacts/scripts/pdf_to_excel_ocr.py`:

- changed no-PDF branch from hard failure to reviewable partial report
- no-PDF report now includes explicit canonical fields:
  - `total_files = 0`
  - `status_counter = {}`
  - `excel_written = false`
  - `output_exists = false`
  - `output_size_bytes = 0`
- no-PDF exit code changed from `2` to `0` (completed with honest partial)

This removes the prior hard-failure semantic drift versus wrapper’s declared
zero-input handling policy.

### 2) Delegate aggregate status now respects partial outcomes

Updated delegate aggregate status computation:

- previous logic:
  - `success` whenever `failed == 0`
- new logic:
  - `success` only when both `failed == 0` and `partial == 0`
  - otherwise `partial`

This prevents overclaiming success when partial file outcomes are present.

### 3) Delegate report now attests output-write evidence explicitly

Updated delegate canonical report fields:

- `excel_written`
- `output_exists`
- `output_size_bytes`

These are emitted consistently across dry-run, no-input, success, and
write-failure paths.

### 4) Wrapper success-evidence gate strengthened

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- `has_strong_delegate_success_evidence()` now additionally requires:
  - no partial file outcomes in `status_counter`
  - `excel_written = true`
  - `output_exists = true`
  - `output_size_bytes > 0`

This makes wrapper-level success claims rely on explicit delegate write
attestation rather than status text alone.

### 5) Focused regressions added for BL-036 semantics

Expanded `tests/test_pdf_to_excel_ocr_delegate.py` with coverage for:

- no-PDF path returns reviewable partial (not hard failure)
- aggregate status stays `partial` when any file is partial
- success reports include explicit output-write evidence fields
- dry-run and write-failure paths emit explicit output evidence defaults

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_delegate.py`
- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`

## Conclusion

`BL-20260325-036` can be treated as complete as a source-side hardening phase.

The wrapper/delegate semantic contract is now materially tighter on:

- zero-input partial semantics
- aggregate status truthfulness
- output-write evidence attestation

Next required step: run a fresh same-origin governed validation to confirm these
semantic hardenings remove the new runtime blocker cluster observed in
`BL-20260325-035`.
