# Runner Contract Alignment Report

## Objective

Complete `BL-20260325-028` by tightening source-side automation contract
instructions so fresh generated inbox runners are less likely to drift from the
reviewed repository behavior on:

- wrapper reuse policy
- delegate JSON report compatibility
- dry-run semantics

This is a contract-hardening phase, not a fresh governed live validation phase.

## Scope

In scope:

- `adapters/local_inbox_adapter.py` automation contract hints/constraints
- focused tests that verify the strengthened contract guidance

Out of scope:

- running a new live Trello governed execute
- changing branch-protection / governance policy
- git finalization and Trello Done writeback

## Changes

### 1) Strengthened automation params

Updated `normalize_local_inbox_payload(...)` automation params to include:

- `preferred_wrapper_script = artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- existing `preferred_base_script = artifacts/scripts/pdf_to_excel_ocr.py`

This clarifies that generation should prefer updating the reviewed wrapper
baseline rather than rewriting control flow from scratch.

### 2) New contract hints for integration consistency

Added explicit contract hints:

- `delegate_report_schema`:
  use `status/total_files/status_counter/dry_run` as canonical delegate evidence
- `delegate_report_handoff`:
  parse delegate JSON printed to stdout directly, not sidecar-only assumptions
- `dry_run_semantics`:
  keep short-circuit dry-run as honest `partial` with `execution.delegated=false`,
  or pass through `--dry-run` explicitly if delegation is used

Also strengthened `reuse_preference` so it explicitly references both reviewed
wrapper and reviewed delegate scripts.

### 3) New constraints and acceptance criteria

Added constraints to require:

- reviewed wrapper reuse when available
- delegate schema compatibility with `status/total_files/status_counter/dry_run`
- stdout JSON handoff compatibility
- explicit dry-run delegated/non-delegated semantics

Added matching acceptance criteria so these requirements are review-visible and
gated.

### 4) Focused test updates

Updated `tests/test_local_inbox_adapter.py` assertions to validate new contract
fields and expectations:

- `preferred_wrapper_script`
- new contract hints (`delegate_report_schema`, `delegate_report_handoff`,
  `dry_run_semantics`)
- new constraints and acceptance criteria related to wrapper reuse/report schema
  alignment

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 -m unittest -v tests/test_trello_readonly_ingress.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-028` can be treated as complete as a contract-hardening phase.

The next correct step is a fresh governed validation phase to measure whether
the strengthened source-side contract reduces integration-level
`critic_verdict=needs_revision` outcomes on a newly generated same-origin
preview candidate.
