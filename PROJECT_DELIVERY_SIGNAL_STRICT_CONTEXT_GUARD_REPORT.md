# Project Delivery Signal Strict Context Guard Report

## Context

`project_delivery_signal.py` was introduced to expose compact delivery triage
signals (`delivery_state`, blocking stage/reason). However, without an explicit
strict mode, a blocked delivery state could still be emitted with missing
blocking context.

## Objective

Add fail-closed strict context validation so non-ready delivery states must
carry both `blocking_stage` and `blocking_reason`.

## Implementation

- `scripts/project_delivery_signal.py`
  - adds `--require-blocking-context`
  - strict behavior:
    - when `delivery_state != ready_for_replay`, both `blocking_stage` and
      `blocking_reason` are required
    - missing context returns exit code `2` with explicit stderr message
- `tests/test_project_delivery_signal.py`
  - adds strict-mode failure case for blocked delivery without signal fields
  - adds strict-mode pass case for ready delivery
- `scripts/premerge_check.sh`
  - now invokes signal extraction with:
    - `--require-delivery-state`
    - `--require-blocking-context`
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - documents strict extraction command and contract expectations

## Verification Snapshot (2026-03-29)

- `python3 -m unittest -v tests/test_project_delivery_signal.py` (passed)
- `bash -n scripts/premerge_check.sh` (passed)
- `python3 scripts/project_delivery_signal.py --status-json /tmp/project_delivery_status_after_bl151.json --require-delivery-state --require-blocking-context --output-format tsv` (passed)

## Outcome

Delivery signal visibility is now fail-closed for blocked states, preventing
silent loss of actionable blocker context in premerge/operator workflows.
