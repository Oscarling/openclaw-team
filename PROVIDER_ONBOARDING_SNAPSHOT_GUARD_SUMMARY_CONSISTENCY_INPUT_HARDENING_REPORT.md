# Provider Onboarding Snapshot Guard Summary Consistency Input Hardening Report

## Objective

Harden summary/report consistency checks by enforcing summary-schema validation
before comparing snapshot-guard metrics.

## Scope

In scope:

- integrate summary validator into
  `provider_onboarding_snapshot_guard_consistency_check.py`
- fail fast on summary schema errors
- add unit test for summary-schema-invalid path
- keep strict repo-path report validation and existing metric checks

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_consistency_check.py`
- supporting validator:
  - `scripts/provider_onboarding_snapshot_guard_summary_validate.py`

## Validation Evidence

- checker now emits `summary validation error:` before metric compare when
  summary payload is malformed.
- tests include:
  - pass path
  - summary/report mismatch path
  - report schema invalid path
  - summary schema invalid path

## Result

Summary/report consistency now has strict input validation on both sides
(summary + report), reducing false confidence from malformed artifacts.

## Decision

BL-099 remains externally blocked; snapshot-guard consistency gates gained
stronger fail-closed input hardening.
