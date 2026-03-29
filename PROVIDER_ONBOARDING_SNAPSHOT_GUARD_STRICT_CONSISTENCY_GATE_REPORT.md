# Provider Onboarding Snapshot Guard Strict Consistency Gate Report

## Objective

Standardize strict repo-path enforcement for snapshot-guard summary/report
consistency checks in both premerge and runbook operations.

## Scope

In scope:

- update premerge invocation to pass `--repo-root` and `--require-repo-paths`
- update runbook command to the same strict invocation
- retain existing consistency semantics

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- premerge update:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- strict-mode-capable checker:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`

## Validation Evidence

- premerge now invokes summary/report consistency check with explicit repo-root
  and path enforcement.
- runbook command mirrors premerge strict invocation for operator parity.

## Result

Snapshot-guard consistency checks now run under uniform strict path policy
across automated gates and manual operations.

## Decision

BL-099 remains externally blocked; local governance workflow now has stricter
and more consistent operator/merge behavior.
