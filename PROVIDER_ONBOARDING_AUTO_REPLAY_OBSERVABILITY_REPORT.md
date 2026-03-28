# Provider Onboarding Auto-Replay Observability Report

## Objective

Keep the retryable rejected preview auto-replay behavior minimal and safe, while
making replay activation visible in execution outputs for faster triage.

## Scope

In scope:

- add explicit replay observability fields to approval execution outputs
- persist the same fields in `.result.json` sidecar
- expose replay trigger reason for retryable rejected previews
- extend tests to cover both replay-used and replay-not-used states

Out of scope:

- replay policy redesign
- retry budget strategy changes
- provider routing / key-base quality changes

## Deliverables

- updated execution script:
  - `skills/execute_approved_previews.py`
- updated tests:
  - `tests/test_execute_approved_previews.py`

## Validation Evidence

- new output fields:
  - `auto_replay_retryable_rejection_used`
  - `auto_replay_retryable_rejection_reason`
- replay gate now returns both decision and reason, then writes fields to:
  - runtime function return payload
  - persisted sidecar (`approvals/<preview_id>.result.json`)
- tests assert:
  - retryable rejected preview replay path sets `used=true` and reason includes
    transient class signal (`http_520`)
  - budget-exhausted replay skip path sets `used=false` and reason empty

## Result

Retryable rejection recovery behavior is now auditable and easier to debug with
no expansion of replay scope beyond existing bounded safety controls.

## Decision

This is a minimal observability enhancement that strengthens operator feedback
without changing the core fail-closed decision model.
