# Project Delivery Status Summary Fallback Alignment Report

Date: 2026-03-29
Owner: Oscarling

## Objective

Keep the delivery-status mainline "run-through" signal stable when operators pass
an outdated/missing onboarding summary path, so status no longer falls back to
`unknown_waiting_signal` in an otherwise completed post-finalization stage.

## Root Cause

`scripts/project_delivery_status.py` only loaded onboarding summary from the
explicit `--summary-json` path. If that path was missing, onboarding state became
empty and delivery-state evaluation dropped into `missing_onboarding_signal`,
even when the canonical default summary file was present and valid.

## Changes

- `scripts/project_delivery_status.py`
  - added `DEFAULT_ONBOARDING_SUMMARY_JSON` constant as the canonical summary path.
  - added `_repo_scoped_path(...)` helper to resolve relative paths under
    `repo_root`.
  - when the requested summary path is missing, automatically falls back to the
    canonical default summary path if it exists.
  - reports the effective summary path via `onboarding_summary_path`.
- `tests/test_project_delivery_status.py`
  - added
    `test_build_status_payload_falls_back_to_default_summary_when_requested_path_missing`
    to enforce fallback behavior and prevent regression.

## Verification

- `python3 -m unittest -v tests/test_project_delivery_status.py` (passed, 10 tests)
- `python3 scripts/project_delivery_status.py --summary-json runtime_archives/bl100/provider_onboarding_summary.json --output-json runtime_archives/bl100/tmp/project_delivery_status_summary_fallback_alignment.json --output-md runtime_archives/bl100/tmp/project_delivery_status_summary_fallback_alignment.md` (passed)
  - output `delivery_state=ready_for_replay`
  - output `onboarding_summary_path=runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
  - output next step remains post-finalization stable-maintenance guidance

## Outcome

Delivery-status output is now resilient to stale summary-path invocations while
preserving existing ready-state semantics and post-finalization guidance.
