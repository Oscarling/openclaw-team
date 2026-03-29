# Provider Onboarding Rejected Auto-Replay Guard Report

## Objective

Add a minimal, controlled auto-replay path so retryable transient failures do
not remain permanently blocked by `rejected` preview status.

## Scope

In scope:

- allow one automatic replay for retryable rejected previews (without requiring
  `--allow-replay`)
- gate auto-replay by bounded attempt budget
- keep existing explicit replay behavior unchanged
- add tests for allowed replay and budget exhaustion

Out of scope:

- queue scheduling redesign
- external provider routing changes
- unlimited replay loops

## Deliverables

- updated execution script:
  - `skills/execute_approved_previews.py`
- updated tests:
  - `tests/test_execute_approved_previews.py`

## Validation Evidence

- new bounded configuration:
  - `ARGUS_AUTO_REPLAY_RETRYABLE_REJECTION_ATTEMPTS`
- retryable rejected previews are auto-replayed only when:
  - previous rejection is classified transient/workspace-recoverable
  - prior execution attempts are within configured budget
- tests cover:
  - one-time auto-replay success path
  - auto-replay budget exhausted skip path

## Result

Transiently rejected previews can self-recover on the next run without manual
`--allow-replay`, while still preserving bounded safety against replay loops.

## Decision

This is a minimal resilience improvement for intermittent instability and does
not change fail-closed behavior for non-retryable rejections.
