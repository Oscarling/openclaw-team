# Provider Onboarding Snapshot Guard Consistency Check Report

## Objective

Ensure snapshot-guard summary metrics remain consistent with row-level
snapshot-guard report metrics under merge-time checks.

## Scope

In scope:

- add dedicated summary/report consistency-check script
- add unit tests for match/mismatch behavior
- integrate consistency check into premerge after guard-report generation
- update runbook command path

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- new script:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`
- new tests:
  - `tests/test_provider_onboarding_snapshot_guard_consistency_check.py`
- premerge integration:
  - `scripts/premerge_check.sh`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- unit coverage verifies both pass and fail paths
- runtime consistency check passes:
  - summary:
    `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
  - report:
    `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`
- premerge now enforces the same check using
  `/tmp/provider_onboarding_snapshot_guard_report_premerge.json`

## Result

Snapshot-guard observability now has an additional fail-closed cross-artifact
gate, reducing risk of summary/report drift.

## Decision

BL-099 remains externally blocked; local governance gained stronger consistency
assurance across snapshot-guard evidence artifacts.
