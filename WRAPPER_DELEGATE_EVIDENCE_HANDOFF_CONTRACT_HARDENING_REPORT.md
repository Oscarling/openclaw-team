# Wrapper Delegate Evidence Handoff Contract Hardening Report

## Objective

Complete `BL-20260325-058` by hardening wrapper/delegate contract behavior
after `BL-20260325-057` critic findings persisted on:

- dry-run propagation recurrence
- stdout-over-sidecar evidence precedence risk

## Scope

In scope:

- harden `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` delegate report
  handoff and source-truth precedence
- tighten generation-side contract guidance in
  `adapters/local_inbox_adapter.py`
- add focused regressions and align adapter contract tests

Out of scope:

- governed live rerun in this phase
- Trello ingest/approval workflow redesign
- unrelated runtime/retry hardening

## Changes

### 1) Sidecar-first delegate report truth in wrapper runtime

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- always passes delegate sidecar path via `--report-json`
- adds sidecar file loader and treats sidecar JSON as canonical evidence
- falls back to stdout JSON only when sidecar evidence is missing
- records report source in summary:
  - `execution.delegate_report_source` (`sidecar|stdout|none`)
  - `execution.delegate_report_sidecar_path`
- emits explicit note when stdout JSON diverges from sidecar and sidecar is
  selected

Effect:

- closes evidence-loss risk from stdout-first parsing when sidecar is available.

### 2) Contract-level hardening for governed generation prompts

Updated `adapters/local_inbox_adapter.py` contract hints/constraints:

- `delegate_report_handoff` now requires sidecar-first canonical behavior with
  stdout fallback only
- `dry_run_semantics` now requires delegated dry-run pass-through for readonly
  governed flows (no pre-delegate short-circuit)
- synchronized matching constraint and acceptance-criteria language

Effect:

- reduces recurrence risk where generated wrapper regresses into ambiguous
  dry-run behavior or weak evidence precedence.

## Test Coverage

Updated `tests/test_pdf_to_excel_ocr_inbox_runner.py`:

- extended fake delegate scripts to accept `--report-json`
- added `test_sidecar_report_is_canonical_when_stdout_diverges`
  to assert sidecar precedence and divergence note
- preserved dry-run delegation regression:
  `test_dry_run_forwards_flag_to_delegate_and_returns_partial`

Updated `tests/test_local_inbox_adapter.py`:

- aligned expectations with sidecar-first and delegated dry-run contract text

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py tests/test_local_inbox_adapter.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-058` is complete as a source-side blocker-hardening phase.

Wrapper evidence handoff now prefers sidecar truth and generation-side contract
guidance is tightened to keep dry-run delegation and report precedence behavior
consistent under governed runtime.

Next required step: run one fresh same-origin governed validation to verify
critic findings move away from these contract gaps.
