# Provider Onboarding History Backfill Gap Reporting

## Objective

Provide a deterministic report of remaining history rows that still miss
`note_class_counts`, including machine-classified reasons.

## Scope

In scope:

- add gap-report script for missing note-count rows
- classify unresolved rows by reason (guard mismatch, missing assessment, parse
  error, etc.)
- integrate report check into premerge (no repo writes)

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- gap-report script:
  - `scripts/provider_onboarding_history_backfill_gaps.py`
- tests:
  - `tests/test_provider_onboarding_history_backfill_gaps.py`
- premerge integration:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- current gap artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_history_backfill_gaps.json`

## Validation Evidence

- current artifact reports one unresolved row:
  - `missing_note_count_rows=1`
  - `reason_counts.guard_mismatch_block_reason=1`
- premerge runs gap-report generation to `/tmp` and passes

## Result

Residual note-signal gaps are now explicitly tracked with reasons, so incomplete
coverage is transparent and actionable.

## Decision

BL-099 remains externally blocked; local governance now includes explicit gap
visibility for conservative backfill outcomes.
