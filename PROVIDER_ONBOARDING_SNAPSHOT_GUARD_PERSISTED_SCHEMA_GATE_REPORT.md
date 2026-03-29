# Provider Onboarding Snapshot Guard Persisted Schema Gate Report

## Objective

Add an explicit premerge gate that validates the persisted snapshot-guard
report artifact schema/path integrity.

## Scope

In scope:

- run persisted report validation in premerge
- enforce repo-scoped path checks for persisted report rows
- document operator command in local runbook

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- premerge gate update:
  - `scripts/premerge_check.sh`
- existing validator reused:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- docs update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- premerge now executes:
  - `provider_onboarding_snapshot_guard_report_validate.py` against
    `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`
    with `--require-repo-paths`
- persisted report remains consistency-checked against history and now also
  schema/path-checked as its own artifact.

## Result

Persisted snapshot-guard report governance is now dual-gated: freshness against
history and structural/path integrity of the persisted file itself.

## Decision

BL-099 remains externally blocked; local evidence chain gained an additional
fail-closed persisted-artifact quality gate.
