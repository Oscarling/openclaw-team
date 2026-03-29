# Project Delivery Signal Bundle Productization Report

## Context

Delivery signal extraction had become multi-step:

1. generate status JSON
2. generate `signal.tsv`
3. generate `signal.json`
4. run consistency checker

Each step was valid, but premerge and manual workflows repeated command wiring.

## Objective

Provide a one-shot bundle command that emits signal artifacts and performs
consistency checks in one deterministic invocation.

## Implementation

- `scripts/project_delivery_signal_bundle.py`
  - inputs:
    - `--status-json`
    - `--output-prefix` (or explicit output paths)
  - strict gates:
    - `--require-delivery-state`
    - `--require-blocking-context`
  - outputs:
    - signal JSON
    - signal TSV
    - optional bundle summary JSON
  - default behavior includes embedded status-vs-signal consistency check
    (opt-out via `--no-consistency-check`)
- `tests/test_project_delivery_signal_bundle.py`
  - pass case for artifact generation + consistency
  - strict fail case for blocked state missing context
  - skip-consistency pass case
- `scripts/premerge_check.sh`
  - now uses bundle command for signal artifact generation
  - keeps concise state/stage/reason visibility from generated TSV row
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - documents one-shot bundle command as recommended path

## Verification Snapshot (2026-03-29)

- `python3 -m unittest -v tests/test_project_delivery_signal_bundle.py` (passed)
- `python3 -m unittest -v tests/test_project_delivery_signal_consistency_check.py tests/test_project_delivery_signal.py tests/test_project_delivery_status.py` (passed)
- `bash -n scripts/premerge_check.sh` (passed)
- `python3 scripts/project_delivery_signal_bundle.py --status-json /tmp/project_delivery_status_after_bl153.json --output-prefix /tmp/project_delivery_status_after_bl153.signal --require-delivery-state --require-blocking-context --output-summary-json /tmp/project_delivery_status_after_bl153.signal.bundle.summary.json` (passed)

## Outcome

Signal artifact generation is now single-entrypoint and consistency-safe,
reducing command drift risk in blocked-provider triage workflows.
