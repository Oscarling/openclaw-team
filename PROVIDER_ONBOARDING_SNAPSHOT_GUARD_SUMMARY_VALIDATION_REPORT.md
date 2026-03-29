# Provider Onboarding Snapshot Guard Summary Validation Report

## Objective

Add a dedicated validator for snapshot-guard summary fields so malformed summary
artifacts fail before merge.

## Scope

In scope:

- create summary validator for snapshot-guard fields
- enforce numeric/range and cross-field invariants
- enforce mismatch-reason key taxonomy and counts
- add unit tests and premerge integration
- document command in runbook

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- new script:
  - `scripts/provider_onboarding_snapshot_guard_summary_validate.py`
- new tests:
  - `tests/test_provider_onboarding_snapshot_guard_summary_validate.py`
- premerge update:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- validator checks:
  - required numeric fields and bounds
  - guard totals vs `assess_rows_with_snapshot`
  - mismatch reason taxonomy and reason-sum parity
  - match-percent formula
- tests cover pass and multiple fail paths (including missing required field).

## Result

Snapshot-guard summary artifacts are now schema-validated with fail-closed
invariants before merge-time consistency checks consume them.

## Decision

BL-099 remains externally blocked; local governance added explicit summary-level
artifact integrity guarantees.
