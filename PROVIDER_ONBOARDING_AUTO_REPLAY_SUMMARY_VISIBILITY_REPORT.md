# Provider Onboarding Auto-Replay Summary Visibility Report

## Objective

Expose retryable-rejection auto-replay usage at run-summary level so operators
can triage execution quality without inspecting every per-preview result.

## Scope

In scope:

- add top-level replay usage count to `execute_approved_previews.main` payload
- add top-level replay reason distribution to same payload
- add unit test coverage for the new summary fields

Out of scope:

- replay policy or retry budget changes
- per-preview decision logic changes
- provider routing adjustments

## Deliverables

- updated runtime script:
  - `skills/execute_approved_previews.py`
- updated tests:
  - `tests/test_execute_approved_previews.py`

## Validation Evidence

- main payload now includes:
  - `auto_replay_retryable_rejection_used`
  - `auto_replay_retryable_rejection_reason_counts`
- reason-count aggregation only counts entries where:
  - `auto_replay_retryable_rejection_used == true`
  - replay reason is non-empty
- test `test_main_emits_auto_replay_summary_counts` verifies:
  - top-level count and reason map
  - existing status counters are preserved

## Result

Run-level observability now directly surfaces replay activation frequency and
trigger distribution, improving operational diagnosis with minimal code change.

## Decision

This is a non-invasive observability enhancement aligned with the current
fail-closed replay model.
