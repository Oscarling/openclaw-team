# Project Delivery Status Require-Ready Gate Report

## Objective

Add a fail-fast readiness gate to the delivery status board so automation can
deterministically stop when the project is not yet ready for replay closure.

## Scope

In scope:

- add `--require-ready` to `project_delivery_status.py`
- return exit code `2` unless `delivery_state=ready_for_replay`
- add unit tests for ready/non-ready exit behavior
- add premerge smoke invocation for delivery status board generation
- document fail-fast usage in onboarding runbook

Out of scope:

- changing provider route probing logic
- changing backlog status source-of-truth rules
- auto-updating blocked backlog items

## Deliverables

- script update:
  - `scripts/project_delivery_status.py`
- tests update:
  - `tests/test_project_delivery_status.py`
- merge gate update:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- `python3 scripts/project_delivery_status.py --repo-root /Users/lingguozhong/openclaw-team --require-ready`
  exits `2` under current blocked state
- unit tests validate:
  - non-ready returns `2`
  - ready returns `0`
- premerge now includes status-board smoke generation and output artifact write

## Result

Status-board output can now be used directly as an automation gate to prevent
premature replay/canary closure steps when readiness is not met.

## Decision

This is a minimal closure-hardening enhancement that improves deterministic
operations without altering existing provider/onboarding decision logic.
