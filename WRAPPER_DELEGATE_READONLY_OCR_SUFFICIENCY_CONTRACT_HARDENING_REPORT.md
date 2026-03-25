# Wrapper/Delegate Readonly + OCR Sufficiency Contract Hardening Report

## Objective

Close `BL-20260325-060` by hardening wrapper/delegate contract semantics after
BL-059 critic findings:

- make readonly scope explicit and non-misleading
- keep no-external-writeback guarantees clear
- prevent wrapper success overclaim when OCR runtime is not fully available in
  OCR-relevant modes (`auto`/`on`)

## Changes

### 1) Wrapper readonly semantics were made explicit

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` summary payload:

- `readonly_attestation.readonly_scope = "no_external_writeback"`
- `readonly_attestation.local_filesystem_writes_allowed = not dry_run`
- clarified readonly statement text so it no longer implies strict filesystem
  readonly when `dry_run=false`
- added explicit note: readonly here means no external writeback; local output
  writes may still happen in non-dry-run mode

### 2) OCR sufficiency was added to wrapper success gating

Updated `has_strong_delegate_success_evidence(...)` in
`artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- when `ocr_mode` is `auto` or `on`
- and delegate report says `ocr_runtime_status` is `partial` or `blocked`
- wrapper now refuses `success` and keeps `partial` with explicit rationale

This avoids overclaiming OCR completeness when runtime dependencies are
incomplete, even if output files exist.

### 3) Generation contract was tightened to reduce recurrence

Updated `adapters/local_inbox_adapter.py` contract text:

- added `contract_hints.readonly_semantics`
- added `contract_hints.ocr_sufficiency`
- extended automation constraints and acceptance criteria to require:
  - explicit no-external-writeback readonly wording
  - conservative partial status when OCR runtime is `blocked/partial` in
    `auto`/`on` modes

## Tests

Updated tests:

- `tests/test_pdf_to_excel_ocr_inbox_runner.py`
  - added `test_ocr_runtime_blocked_keeps_wrapper_partial_even_with_success_attestation`
  - extended readonly attestation assertions for new fields
- `tests/test_local_inbox_adapter.py`
  - added assertions for new contract hints, constraints, and acceptance criteria

Validation run:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py tests/test_local_inbox_adapter.py`
  - passed (`16/16`)

## Outcome

`BL-20260325-060` source-side hardening is complete:

- readonly semantics are explicit and bounded
- OCR sufficiency risk is now captured in wrapper success policy
- generation-side contract text enforces the same semantics for future
  automation output stability
