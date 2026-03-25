# Wrapper/Delegate Execution Outcome-Contract + Diagnostics Completeness Hardening Report

## Objective

Close `BL-20260325-066` by hardening wrapper/delegate behavior after
`BL-20260325-065` critic findings:

- make wrapper subprocess exit-code handling deterministic and strict
- canonicalize no-input/partial/failed semantics between wrapper and delegate
- preserve relevant stdout/stderr diagnostics in structured wrapper evidence

## Scope

In scope:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` outcome-contract and
  diagnostics hardening
- focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- backlog/worklog synchronization for blocker completion

Out of scope:

- governed live rerun in this blocker phase
- Trello workflow redesign
- OCR extraction algorithm changes in delegate internals

## Changes

### 1) Non-zero delegate exit code is now a hard wrapper failure signal

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- made non-dry-run non-zero delegate return code a hard-failure branch
- added explicit override note when delegate JSON reports `success`/`partial`
  but subprocess exit code is non-zero
- kept final wrapper exit contract deterministic:
  - `success`/`partial` -> process exit `0`
  - `failed` -> process exit `1`

Effect:

- wrapper outcome no longer risks softening delegate process-level failure
  semantics.

### 2) Canonical partial semantics are preserved without XLSX output

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- when delegate exits `0` and reports `status=partial`, wrapper now preserves
  `partial` even when workbook output does not exist
- retained stricter `failed` handling for explicit `status=failed`
- retained conservative `failed` handling for contradictory `status=success`
  without workbook artifact

Effect:

- no-input / best-effort partial outcomes remain canonical across
  wrapper/delegate and are not collapsed into wrapper `failed` by missing XLSX
  alone.

### 3) Structured diagnostics now preserve stdout/stderr evidence fields

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- added execution diagnostics fields:
  - `stdout_present`, `stderr_present`
  - `stdout_line_count`, `stderr_line_count`
  - `stdout_excerpt`, `stderr_excerpt`
- added deterministic excerpt truncation for large logs
- added explicit note when stderr was captured and preserved

Effect:

- reviewer can audit delegate diagnostics directly from wrapper summary payload
  without relying only on ad-hoc log interpretation.

## Tests

Updated tests in `tests/test_pdf_to_excel_ocr_inbox_runner.py`:

- `test_preserves_delegate_partial_without_output_when_exit_zero`
- `test_nonzero_delegate_exit_hard_fails_even_with_structured_json`
- `test_preserves_stdout_stderr_diagnostics_in_summary`

Validation runs:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - passed (`18/18`)
- `python3 scripts/backlog_lint.py`
  - passed
- `python3 scripts/backlog_sync.py`
  - passed

## Outcome

`BL-20260325-066` source-side hardening is complete:

- wrapper/delegate execution outcome contract is stricter on non-zero exits
- wrapper/delegate partial semantics are more canonical in no-output
  best-effort paths
- wrapper summary now preserves diagnostics completeness via explicit
  stdout/stderr evidence fields
