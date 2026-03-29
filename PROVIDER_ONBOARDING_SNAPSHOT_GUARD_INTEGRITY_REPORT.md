# Provider Onboarding Snapshot Guard Integrity Report

## Objective

Expose decision-field drift between history rows and immutable snapshot payloads
as explicit summary metrics and consistency-gated evidence.

## Scope

In scope:

- extend onboarding history summary with snapshot-guard match/mismatch metrics
- include those metrics in summary consistency checks
- keep repo-only filtering semantics requiring repo-scoped snapshot paths for
  `assess` rows
- update tests and runbook guidance

Out of scope:

- external provider/key remediation
- replay/canary execution

## Deliverables

- summary hardening:
  - `scripts/provider_onboarding_history_summary.py`
- consistency hardening:
  - `scripts/provider_onboarding_history_consistency_check.py`
- tests:
  - `tests/test_provider_onboarding_history_summary.py`
  - `tests/test_provider_onboarding_history_consistency_check.py`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- summary now emits:
  - `assess_rows_with_snapshot_guard_match`
  - `assess_rows_with_snapshot_guard_mismatch`
  - `assess_rows_with_snapshot_guard_unverified`
  - `assess_snapshot_guard_match_percent`
- consistency check now compares all fields above and fails on mismatch
- refreshed repo summary currently reports:
  - `assess_rows_with_snapshot_guard_match=1`
  - `assess_rows_with_snapshot_guard_mismatch=1`
  - `assess_snapshot_guard_match_percent=50.0`

## Result

Snapshot integrity is now observable in merge-gated summary evidence, making
legacy drift visible without requiring external provider availability.

## Decision

BL-099 remains externally blocked; local governance now quantifies snapshot
guard integrity and keeps the signal under consistency enforcement.
