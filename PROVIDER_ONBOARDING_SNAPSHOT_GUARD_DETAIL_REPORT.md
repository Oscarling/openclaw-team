# Provider Onboarding Snapshot Guard Detail Report

## Objective

Add row-level snapshot guard drift diagnostics so operators can inspect concrete
mismatch rows and reasons under repo-only governance.

## Scope

In scope:

- add a dedicated snapshot guard detail report script
- report both aggregate reason counts and per-row mismatch details
- integrate script + tests into premerge
- document local runbook usage

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- new script:
  - `scripts/provider_onboarding_snapshot_guard_report.py`
- new tests:
  - `tests/test_provider_onboarding_snapshot_guard_report.py`
- premerge integration:
  - `scripts/premerge_check.sh`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- generated report:
  - `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`
- current repo report shows:
  - `guard_match_rows=1`
  - `guard_mismatch_rows=1`
  - `reason_counts={"guard_match": 1, "guard_mismatch_block_reason": 1}`
  - one row-level mismatch entry under `non_match_rows`

## Result

Snapshot guard drift is now visible at both summary and row-detail levels, so
legacy mismatch triage no longer requires manual ad-hoc inspection.

## Decision

BL-099 remains externally blocked; local evidence governance now includes
deterministic row-level drift reporting under merge-time checks.
