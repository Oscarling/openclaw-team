# Wrapper Dry-Run Delegate Propagation Hardening Report

## Objective

Complete `BL-20260325-056` by hardening wrapper dry-run semantics after
`BL-20260325-055` critic verdict `needs_revision` reported that dry-run intent
was not propagated through the wrapper/delegate path.

## Scope

In scope:

- harden `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` dry-run path
- preserve readonly/best-effort partial semantics
- add focused regression for dry-run delegate flag propagation

Out of scope:

- governed live rerun in this phase
- non-dry-run workflow redesign
- Trello ingest/approval pipeline changes

## Changes

### 1) Forward dry-run intent to the reviewed delegate

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- removed the early dry-run short-circuit before delegate execution
- when `--dry-run true` is requested, wrapper now appends `--dry-run` to
  delegate command
- wrapper records explicit note that dry-run is forwarded end-to-end

Effect:

- wrapper/delegate pair now carries dry-run semantics explicitly instead of
  dropping them before delegate handoff.

### 2) Preserve conservative partial semantics for dry-run delegate outcomes

Updated dry-run result handling in wrapper:

- if delegate returns `0` under dry-run, wrapper status remains `partial`
- wrapper no longer misclassifies dry-run as missing XLSX failure path
- wrapper records whether delegate report attests `dry_run=true`

Effect:

- dry-run validation remains reviewable and truthful without overclaiming real
  conversion success.

## Test Coverage

Updated `tests/test_pdf_to_excel_ocr_inbox_runner.py`:

- replaced dry-run regression with
  `test_dry_run_forwards_flag_to_delegate_and_returns_partial`

This test validates:

- wrapper delegates under dry-run
- delegate command includes `--dry-run`
- delegate report carries `dry_run=true`
- wrapper final status remains `partial`

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py` (10/10)
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-056` is complete as a source-side blocker-hardening phase.

Wrapper dry-run intent now propagates through the reviewed delegate path and
preserves conservative partial semantics with explicit evidence.

Next required step: run one fresh same-origin governed validation to confirm
critic findings move away from dry-run propagation concerns.
