# Provider Onboarding Snapshot Guard Persisted Report Consistency Report

## Objective

Ensure persisted snapshot-guard report JSON remains fresh against onboarding
history by adding a fail-closed recomputation consistency check.

## Scope

In scope:

- add dedicated persisted-report consistency-check script
- recompute expected report from history and compare key fields
- add unit coverage for pass/fail paths
- integrate check into premerge
- update runbook commands

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- new script:
  - `scripts/provider_onboarding_snapshot_guard_report_consistency_check.py`
- new tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_consistency_check.py`
- premerge integration:
  - `scripts/premerge_check.sh`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- unit tests cover:
  - matching report/history pass path
  - stale report mismatch fail path
- runtime consistency check passes for persisted artifact:
  - history:
    `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
  - report:
    `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`
- premerge now enforces persisted-report freshness against history.

## Result

Snapshot-guard evidence now includes freshness protection for persisted report
artifacts, preventing stale row-level drift data from silently propagating.

## Decision

BL-099 remains externally blocked; local governance chain now verifies both
report shape and report freshness before merge.
