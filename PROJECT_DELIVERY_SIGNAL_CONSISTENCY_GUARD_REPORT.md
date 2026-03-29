# Project Delivery Signal Consistency Guard Report

## Context

`project_delivery_signal.py` now emits strict blocked-context output, but
premerge previously relied on direct extraction artifacts without an explicit
cross-artifact parity check against source status JSON.

## Objective

Add a dedicated consistency checker so status JSON and signal artifacts
(`signal.json` / `signal.tsv`) are validated against the same canonical signal
contract.

## Implementation

- `scripts/project_delivery_signal_consistency_check.py`
  - computes expected signal from `--status-json`
  - validates one or both of:
    - `--signal-json`
    - `--signal-tsv`
  - fails with exit code `2` on field-level mismatch
- `tests/test_project_delivery_signal_consistency_check.py`
  - pass case for matching JSON+TSV
  - fail case for JSON drift
  - fail case for TSV drift
  - guard case for missing artifact inputs
- `scripts/premerge_check.sh`
  - runs signal bundle command to generate both artifacts with embedded
    consistency checks:
    - `/tmp/project_delivery_status_premerge.signal.tsv`
    - `/tmp/project_delivery_status_premerge.signal.json`
  - separate consistency checker remains available for explicit/manual audits
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - documents consistency check command usage

## Verification Snapshot (2026-03-29)

- `python3 -m unittest -v tests/test_project_delivery_signal_consistency_check.py` (passed)
- `python3 -m unittest -v tests/test_project_delivery_signal.py tests/test_project_delivery_status.py` (passed)
- `bash -n scripts/premerge_check.sh` (passed)
- `python3 scripts/project_delivery_signal_consistency_check.py --status-json /tmp/project_delivery_status_after_bl151.json --signal-json /tmp/project_delivery_status_after_bl151.signal.json --signal-tsv /tmp/project_delivery_status_after_bl151.signal.tsv` (passed)

## Outcome

Delivery signal artifacts are now parity-checked against source status payloads,
closing a drift gap in blocked-provider observability flow without altering
merge gate policy.
