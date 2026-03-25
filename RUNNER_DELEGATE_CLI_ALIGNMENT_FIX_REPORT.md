# Runner Delegate CLI Alignment Fix Report

## Objective

Complete `BL-20260325-030` by removing the wrapper/delegate CLI contract drift
identified in `BL-20260325-029`, where generated wrappers could pass
`--report-json` while the reviewed delegate did not accept that argument.

## Scope

In scope:

- harden reviewed delegate CLI compatibility for report handoff
- ensure report emission remains deterministic and reviewable
- add focused regression coverage for `--report-json` behavior

Out of scope:

- fresh governed live Trello validation run
- changes to preview/approval governance policy
- git finalization / Trello Done writeback

## Changes

### 1) Added optional `--report-json` to reviewed delegate

Updated `artifacts/scripts/pdf_to_excel_ocr.py`:

- parse new optional argument:
  - `--report-json <path>`
- keep stdout JSON behavior unchanged
- write the same JSON payload to sidecar path when provided

This makes the reviewed delegate CLI-compatible with wrappers that include
`--report-json`.

### 2) Unified report emission across all delegate exit paths

Introduced `emit_report(...)` in `artifacts/scripts/pdf_to_excel_ocr.py` and
used it for:

- discovery failure path
- empty-input failure path
- dry-run success path
- normal success path
- write failure path

Result: sidecar report output is deterministic wherever a JSON report is
already emitted to stdout.

### 3) Added focused regression tests

Added `tests/test_pdf_to_excel_ocr_delegate.py`:

- `test_report_json_is_written_for_dry_run`
- `test_report_json_is_written_on_write_failure`

These verify stdout and sidecar parity and confirm compatibility behavior under
both success-like and failure-like paths.

### 4) Updated usage documentation

Updated `artifacts/docs/pdf_to_excel_ocr_usage.md` to document:

- `--report-json` argument and semantics

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_delegate.py`
- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`

## Conclusion

`BL-20260325-030` can be treated as complete as a source-side contract fix
phase.

The reviewed delegate now accepts `--report-json`, removing the specific CLI
mismatch found in `BL-20260325-029`. The next correct step is a fresh governed
validation run on a same-origin regenerated candidate to confirm the runtime
outcome end-to-end under the aligned contract.
