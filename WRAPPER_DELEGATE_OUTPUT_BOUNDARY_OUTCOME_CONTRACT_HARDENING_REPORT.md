# Wrapper/Delegate Output-Boundary + Outcome-Contract Hardening Report

## Objective

Close `BL-20260325-064` by hardening wrapper/delegate behavior after
`BL-20260325-063` critic findings:

- constrain wrapper output destination policy for governed readonly runs
- clarify extraction-vs-export semantics so failure diagnostics are explicit
  and not collapsed into ambiguous aggregate signals

## Scope

In scope:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` output-boundary and
  diagnostic hardening
- `artifacts/scripts/pdf_to_excel_ocr.py` extraction/export phase semantics
  hardening
- focused regressions for boundary enforcement and phase-distinction signals

Out of scope:

- governed live rerun in this blocker phase
- Trello workflow redesign
- unrelated OCR extraction algorithm changes

## Changes

### 1) Wrapper output destination is now constrained to approved root

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- added approved boundary root:
  - `APPROVED_OUTPUT_ROOT = <repo>/artifacts/outputs`
- added `resolve_output_path(...)` and recorded output resolution provenance in
  summary payload
- enforced boundary before delegate execution:
  - when `output_xlsx` is outside approved root, wrapper fails fast and refuses
    broader local write destination in governed readonly flow
- exposed contract fields:
  - `contract.approved_output_root`
  - `contract.output_boundary_enforced`

Effect:

- wrapper no longer permits arbitrary host-path write destinations by default in
  governed readonly runs.

### 2) Delegate report now distinguishes extraction and export phases

Updated `artifacts/scripts/pdf_to_excel_ocr.py`:

- normalized report schema now includes:
  - `extraction_status`
  - `export_status`
- discovery/no-input exits now set explicit phase statuses (`none`,
  `not_started`/`skipped_no_input`)
- dry-run path sets `export_status=skipped_dry_run`
- write phase now tracks:
  - `export_status=running|succeeded|failed`
- Excel write failure now emits explicit distinction notes:
  - extraction phase outcome remains visible
  - export failure is explicit with actionable next steps

Effect:

- consumers can differentiate extraction evidence from workbook export outcome
  without guessing from coarse aggregate status.

### 3) Wrapper summary now surfaces delegate phase outcomes explicitly

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- added `extract_delegate_phase_statuses(...)`
- records delegate phase outcomes under:
  - `execution.delegate_extraction_status`
  - `execution.delegate_export_status`
- emits explicit notes when:
  - delegate phase outcomes are known
  - export failed after extraction evidence exists

Effect:

- runtime summaries now preserve extraction-vs-export diagnostic clarity even
  when final wrapper status is failed.

## Tests

Updated tests:

- `tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - `test_rejects_output_path_outside_approved_root`
  - `test_surfaces_delegate_extraction_export_phase_distinction`
- `tests/test_pdf_to_excel_ocr_script.py`
  - `test_main_excel_write_failure_exposes_extraction_export_distinction`

Validation run:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_script.py tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - passed (`20/20`)

## Outcome

`BL-20260325-064` source-side hardening is complete:

- wrapper output writes are bounded to approved artifact root for governed
  readonly execution
- delegate/wrapper reports now expose extraction and export phase semantics as
  first-class diagnostic evidence
- focused regressions cover both boundary and phase-distinction hardening
