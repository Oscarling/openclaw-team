# Provider Onboarding History Consistency Hardening Report

## Objective

Guarantee that committed onboarding summary JSON stays synchronized with source
history JSONL under the same filtering rules.

## Scope

In scope:

- add deterministic consistency checker for history vs summary
- compare key summary fields and latest snapshot
- integrate checker into premerge fail-closed flow

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- consistency script:
  - `scripts/provider_onboarding_history_consistency_check.py`
- test coverage:
  - `tests/test_provider_onboarding_history_consistency_check.py`
- merge gate integration:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- checker passes for current repo artifacts:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
- test suite validates both match and mismatch paths:
  - `tests/test_provider_onboarding_history_consistency_check.py`
- premerge now blocks stale summary snapshots automatically

## Result

History summary staleness is now detectable and merge-blocking, preventing silent
drift between evidence source and summary snapshot.

## Decision

BL-099 remains externally blocked; local evidence-governance hardening advances
with explicit history-summary consistency guarantees.
