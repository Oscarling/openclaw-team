# Provider Onboarding Snapshot Guard Persisted Summary Schema Hardening Report

## Objective

Harden persisted snapshot-guard report consistency checks by validating summary
schema before optional summary/report consistency comparison.

## Scope

In scope:

- add summary-validator module loading in
  `provider_onboarding_snapshot_guard_report_consistency_check.py`
- validate summary with strict path flags when `--summary-json` is provided
- fail fast with `summary validation error:` before summary/report comparison
- add unit test covering summary-schema-invalid path

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_report_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_consistency_check.py`

## Validation Evidence

- `--summary-json` path now enforces summary schema before parity checks
- strict path mode is inherited from existing `--repo-root --require-repo-paths`
  invocation in premerge/runbook
- tests include new summary-schema-invalid fail case

## Result

Persisted snapshot-guard report consistency now validates both persisted report
schema and optional summary schema before cross-artifact comparisons.

## Decision

BL-099 remains externally blocked; persisted-consistency path gained stronger
fail-closed summary input hardening.
