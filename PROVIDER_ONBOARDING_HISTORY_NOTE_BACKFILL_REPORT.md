# Provider Onboarding History Note Backfill Report

## Objective

Recover note-level signal continuity for legacy onboarding history rows that
predate `note_class_counts` persistence.

## Scope

In scope:

- add conservative history backfill tool
- backfill only when assessment and history decision fields match
- expose dry-run mode for safe premerge checks
- apply backfill to current repo history and refresh summary

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- backfill script:
  - `scripts/provider_onboarding_history_backfill.py`
- tests:
  - `tests/test_provider_onboarding_history_backfill.py`
- merge gate integration:
  - `scripts/premerge_check.sh` (unit + dry-run invocation)
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- refreshed evidence:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

## Validation Evidence

- live backfill run summary:
  - `backfilled=1`
  - `skipped_guard_mismatch=1`
  - `remaining_missing_note_counts=1`
- refreshed summary now reports:
  - `rows_with_note_class_counts=1`
  - `rows_missing_note_class_counts=1`
  - `note_signal_coverage_percent=50.0`
- validator and consistency checks continue to pass

## Result

History note-signal coverage increased from `0.0%` to `50.0%` without
overwriting mismatched legacy rows.

## Decision

BL-099 remains externally blocked; local evidence quality improved with guarded
historical backfill and measurable coverage uplift.
