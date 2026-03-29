# Project Delivery Blocking Reason Canonicalization Report

## Context

Runtime and provider onboarding assessment flows already classify provider billing
failures as `provider_account_arrearage`. Delivery-status post-handshake inference
still emitted `provider_billing_arrearage`, creating avoidable reason-token drift.

## Changes

- Updated `scripts/project_delivery_status.py`:
  - Canonicalized post-handshake arrearage inference to
    `provider_account_arrearage`.
  - Added alias coverage for `Arrearage`, `overdue-payment`, and
    `overdue payment` in backlog source/evidence text.
- Updated `tests/test_project_delivery_status.py`:
  - Existing arrearage promotion-stage assertion now checks canonical reason.
  - Added regression test for `overdue-payment` alias mapping.

## Verification

- `python3 -m unittest -v tests/test_project_delivery_status.py`
- `python3 -m unittest -v tests/test_project_delivery_signal.py tests/test_project_delivery_signal_bundle.py tests/test_project_delivery_signal_consistency_check.py`
- `python3 scripts/project_delivery_status.py --backlog PROJECT_BACKLOG.md --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json --repo-root /Users/lingguozhong/openclaw-team --output-json /tmp/project_delivery_status_after_bl155_canonical.json --output-md /tmp/project_delivery_status_after_bl155_canonical.md`
- `python3 scripts/project_delivery_signal.py --status-json /tmp/project_delivery_status_after_bl155_canonical.json --output-format json > /tmp/project_delivery_signal_after_bl156.json`

All checks passed on 2026-03-29.

## Outcome

Delivery blocking reason taxonomy is now aligned across runtime, onboarding
assessment, status board, and signal extraction outputs, reducing downstream
consumer drift and simplifying triage automation.
