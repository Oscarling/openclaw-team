# Provider Onboarding Snapshot Guard Reason Row Reconciliation Report

## Objective

Ensure snapshot-guard aggregate reason counts exactly reconcile with row-level
non-match reasons.

## Scope

In scope:

- enforce per-reason reconciliation between `reason_counts` and
  `non_match_rows`
- keep existing taxonomy and count-partition checks
- extend validator tests for reconciliation drift failures

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated validator:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_validate.py`
- inherited gate:
  - `scripts/premerge_check.sh`

## Validation Evidence

- validator now fails when any non-match reason count in `reason_counts` does
  not match row-level frequency in `non_match_rows`.
- targeted unit test covers reconciliation drift path.

## Result

Aggregate mismatch diagnostics and row-level details are now strictly
reconciled, reducing silent drift between summary counts and row evidence.

## Decision

BL-099 remains externally blocked; local snapshot-guard governance gained
lossless reason-level reconciliation checks.
