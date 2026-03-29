# Provider Onboarding History Validation Hardening Report

## Objective

Introduce deterministic schema/path validation for onboarding history JSONL so
evidence quality is checked before merge.

## Scope

In scope:

- add a dedicated history validation script
- validate core fields, value shapes, and optional counters
- support repo-path enforcement for committed evidence
- integrate checks into unit tests and premerge gate

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- validation script:
  - `scripts/provider_onboarding_history_validate.py`
- tests:
  - `tests/test_provider_onboarding_history_validate.py`
- merge gate integration:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- validation script passes against current history artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
- dedicated test suite verifies valid, invalid, and repo-path-required cases:
  - `tests/test_provider_onboarding_history_validate.py`
- premerge now fails closed if history structure/path integrity regresses

## Result

History integrity is now enforced by automation, reducing the risk of malformed
or non-repo evidence entering blocker trend records.

## Decision

BL-099 remains blocked on external provider onboarding inputs; local governance
hardening progressed with explicit history schema controls.
