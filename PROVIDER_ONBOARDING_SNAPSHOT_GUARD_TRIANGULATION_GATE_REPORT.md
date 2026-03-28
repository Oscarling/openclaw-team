# Provider Onboarding Snapshot Guard Triangulation Gate Report

## Objective

Unify persisted snapshot-guard consistency checks so one gate validates report
integrity against both history and summary.

## Scope

In scope:

- extend report-consistency checker with optional `--summary-json`
- enforce summary/report consistency inside the same persisted-report check path
- update premerge to use unified triangulation check
- update runbook command and tests

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_report_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_consistency_check.py`
- premerge update:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- checker now supports:
  - `--summary-json <path>`
  - fails on summary/report mismatches in same invocation
- tests cover:
  - summary-consistent pass path
  - summary-mismatch fail path
- premerge now checks persisted report against history and summary via one
  unified command.

## Result

Persisted snapshot-guard gates now use a triangulated consistency path, reducing
check divergence and improving operational coherence.

## Decision

BL-099 remains externally blocked; local governance gained a tighter persisted
artifact consistency gate.
