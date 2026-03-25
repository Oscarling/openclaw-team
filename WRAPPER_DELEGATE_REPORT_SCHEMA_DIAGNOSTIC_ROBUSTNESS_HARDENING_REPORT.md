# Wrapper/Delegate Report-Schema Diagnostic Robustness Hardening Report

## Objective

Close `BL-20260325-062` by hardening wrapper/delegate diagnostics after
`BL-20260325-061` critic findings:

- normalize delegate JSON report schema across sparse failure paths
- ensure wrapper notes surface delegate `error` context explicitly instead of
  only generic evidence-gate messages

## Scope

In scope:

- `artifacts/scripts/pdf_to_excel_ocr.py` report-schema normalization
- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` diagnostic surfacing
- focused regression tests for the two hardening targets

Out of scope:

- governed live rerun/critic validation in this blocker phase
- Trello workflow changes
- unrelated OCR extraction logic changes

## Changes

### 1) Delegate report schema was normalized for failure exits

Updated `artifacts/scripts/pdf_to_excel_ocr.py`:

- added a shared `build_report_template(...)` used by all report exits
- discovery-failure exit now emits full schema with:
  - `status`, `total_files`, `status_counter`, `dry_run`
  - `excel_written`, `output_exists`, `output_size_bytes`
  - `ocr_runtime_status`, `notes`, `next_steps`, `error`
- no-PDF and normal execution exits now share the same schema baseline

Effect:

- wrapper/delegate contract no longer depends on sparse-field failure payloads.

### 2) Wrapper now surfaces delegate error context explicitly

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- added `extract_delegate_error(...)`
- when delegate report includes `error`, wrapper appends explicit diagnostic
  note:
  - `Delegate reported error: ...`

Effect:

- review artifacts keep the delegate’s concrete failure reason visible even when
  evidence gates also fail.

## Tests

Updated tests:

- `tests/test_pdf_to_excel_ocr_script.py`
  - added `test_main_discovery_failure_emits_normalized_failed_schema`
- `tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - added `test_surfaces_delegate_error_context_in_wrapper_notes`

Validation run:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_script.py tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - passed (`17/17`)

## Outcome

`BL-20260325-062` source-side hardening is complete:

- delegate report schema is consistent across success/partial/failure exits
- wrapper diagnostics now preserve delegate `error` context explicitly
- regression coverage exists for both hardening points
