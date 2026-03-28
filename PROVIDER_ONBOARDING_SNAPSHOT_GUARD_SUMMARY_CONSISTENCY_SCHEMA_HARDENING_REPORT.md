# Provider Onboarding Snapshot Guard Summary Consistency Schema Hardening Report

## Objective

Harden snapshot-guard summary/report consistency checks by validating guard
report schema/path integrity before metric comparison.

## Scope

In scope:

- add report-validator integration into summary/report consistency checker
- add `--repo-root` and `--require-repo-paths` controls
- add unit coverage for schema-invalid report failures

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_consistency_check.py`
- reused validator:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`

## Validation Evidence

- checker now fails early when report schema/path validation fails.
- checker continues to fail on summary/report metric drift.
- tests cover:
  - pass path
  - summary/report mismatch path
  - schema-invalid report path

## Result

Summary/report consistency checks now guarantee both semantic metric alignment
and structural integrity of input report artifacts.

## Decision

BL-099 remains externally blocked; local snapshot-guard governance gained
stronger consistency-check input validation.
