# Provider Onboarding Note-Signal Coverage Metrics Report

## Objective

Expose explicit coverage metrics for note-level signal persistence in onboarding
history summaries, so missing signal data is visible instead of implicit.

## Scope

In scope:

- add note-signal coverage metrics to history summary JSON
- extend consistency checks to include new metrics
- update tests and runbook to reflect metric semantics

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- summary metrics update:
  - `scripts/provider_onboarding_history_summary.py`
- consistency check update:
  - `scripts/provider_onboarding_history_consistency_check.py`
- tests:
  - `tests/test_provider_onboarding_history_summary.py`
  - `tests/test_provider_onboarding_history_consistency_check.py`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- refreshed artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

## Validation Evidence

- summary now emits:
  - `rows_with_note_class_counts`
  - `rows_missing_note_class_counts`
  - `note_signal_coverage_percent`
- consistency checker passes with these metrics included in key-field compare
- tests cover 100% and 0% coverage cases

## Result

Summary now reports note-signal coverage explicitly, making historical blind
spots visible and measurable.

## Decision

BL-099 remains externally blocked; local governance now quantifies note-signal
completeness in blocker evidence summaries.
