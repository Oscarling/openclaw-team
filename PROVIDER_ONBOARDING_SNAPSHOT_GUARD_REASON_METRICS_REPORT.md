# Provider Onboarding Snapshot Guard Reason Metrics Report

## Objective

Make snapshot-guard drift actionable by exposing mismatch reasons in summary
metrics instead of only aggregate mismatch counts.

## Scope

In scope:

- extend summary metrics with mismatch reason distribution
- keep consistency checks aligned with the new reason field
- update tests and runbook interpretation guidance

Out of scope:

- external provider/key remediation
- replay/canary execution

## Deliverables

- summary update:
  - `scripts/provider_onboarding_history_summary.py`
- consistency update:
  - `scripts/provider_onboarding_history_consistency_check.py`
- tests:
  - `tests/test_provider_onboarding_history_summary.py`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- summary now emits:
  - `assess_snapshot_guard_mismatch_reason_counts`
- consistency check includes this field in fail-closed comparison
- refreshed summary artifact reports:
  - `assess_snapshot_guard_mismatch_reason_counts={"block_reason": 1}`

## Result

Snapshot drift is now not only detectable but also attributable to concrete
decision fields, improving local remediation planning while BL-099 remains
blocked.

## Decision

Local-first governance is strengthened further with reason-level drift signals
under the same merge-gated summary/consistency chain.
