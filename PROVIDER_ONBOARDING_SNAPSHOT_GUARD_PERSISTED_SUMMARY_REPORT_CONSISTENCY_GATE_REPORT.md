# Provider Onboarding Snapshot Guard Persisted Summary Report Consistency Gate Report

## Objective

Add a premerge gate ensuring persisted snapshot-guard summary/report artifacts
remain mutually consistent.

## Scope

In scope:

- run summary/report consistency check against persisted runtime artifacts
- keep generated premerge report consistency check unchanged
- record governance update in runbook and logs

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- premerge update:
  - `scripts/premerge_check.sh`
- reused consistency checker:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`
- docs update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- premerge now checks:
  - generated report vs summary (`/tmp/...` path)
  - persisted report vs persisted summary
- persisted consistency passes on current artifacts:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
  - `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`

## Result

Cross-artifact consistency governance now covers both generated and persisted
snapshot-guard summary/report pairs.

## Decision

BL-099 remains externally blocked; local evidence chain gained a stronger
persisted-artifact consistency gate.
