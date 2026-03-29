# Provider Onboarding Snapshot Coverage Summary Report

## Objective

Make immutable snapshot adoption measurable in onboarding history summaries and
fail-closed consistency checks.

## Scope

In scope:

- extend summary metrics with assess-row snapshot coverage
- include latest-row `assessment_snapshot_json` in summary snapshot
- enforce repo-only summary filtering to require repo-scoped snapshot paths for
  `assess` rows
- extend consistency checks/tests to include new snapshot coverage fields

Out of scope:

- provider/key remediation
- replay/canary execution

## Deliverables

- summary updates:
  - `scripts/provider_onboarding_history_summary.py`
- consistency updates:
  - `scripts/provider_onboarding_history_consistency_check.py`
- tests:
  - `tests/test_provider_onboarding_history_summary.py`
  - `tests/test_provider_onboarding_history_consistency_check.py`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- summary now emits:
  - `assess_entry_count`
  - `assess_rows_with_snapshot`
  - `assess_rows_missing_snapshot`
  - `assess_snapshot_coverage_percent`
  - `latest.assessment_snapshot_json`
- repo summary artifact confirms current snapshot coverage is `100.0%` for
  assess rows
- consistency checker compares these fields and fails on mismatch

## Result

Onboarding summary now surfaces snapshot-adoption health directly, so immutable
history guarantees remain continuously observable and merge-gated.

## Decision

BL-099 remains externally blocked; local evidence governance gained snapshot
coverage observability without requiring external provider availability.
