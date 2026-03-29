# Premerge Provider Arrearage Advisory Report

## Context

Delivery signal now consistently classifies provider billing blockers as
`provider_account_arrearage`. Premerge output still emitted only a generic
blocked warning, which can lead to repeated replay attempts despite a known
non-retryable external blocker.

## Changes

- Updated `scripts/premerge_check.sh` signal warning section:
  - Retains existing generic warning for non-ready delivery state.
  - Adds a targeted advisory when `signal_reason=provider_account_arrearage`:
    - pause replay retries
    - restore provider account standing before rerun
  - Fixes signal TSV parsing to explicitly read all 5 columns, ensuring
    `signal_reason` is not contaminated by trailing fields and advisory matching
    remains deterministic.
- No pass/fail gate policy was changed.

## Verification

- `bash -n scripts/premerge_check.sh`
- `python3 scripts/backlog_lint.py`

Both checks passed on 2026-03-29.

## Outcome

Premerge triage now includes actionable guidance for arrearage-blocked states,
reducing avoidable replay churn while preserving existing governance gates.
