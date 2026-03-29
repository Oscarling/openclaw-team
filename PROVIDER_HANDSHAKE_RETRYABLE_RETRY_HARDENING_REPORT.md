# Provider Handshake Retryable Retry Hardening Report

## Objective

Reduce false blocked outcomes under unstable provider/base network conditions by
adding bounded retry only for retryable probe failures.

## Scope

In scope:

- add `--retry-attempts` to `provider_handshake_probe.py` (default `2`)
- retry only retryable failure classes (`000`, `5xx`, transport timeout/TLS/DNS)
- keep non-retry behavior for auth-policy `4xx` (`401/403`)
- keep readiness fail-closed (`2xx + api_like`) unchanged
- add dedicated unit tests for retry boundaries
- document retry control in runbook

Out of scope:

- changing provider credentials or upstream proxy policies
- relaxing existing readiness criteria
- adding multi-step capability probes

## Deliverables

- probe hardening:
  - `scripts/provider_handshake_probe.py`
- tests hardening:
  - `tests/test_provider_handshake_probe.py`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- default probe behavior now uses bounded retry (`--retry-attempts 2`)
- `401/403` paths are not retried, preserving quick fail behavior for auth
  issues
- `--retry-attempts 1` preserves strict single-shot behavior
- invalid retry value (`0`) exits with code `2`
- unit coverage validates:
  - transient `000` then `200` succeeds via retry
  - `401` stays single-attempt
  - single-attempt mode disables retry

## Result

Probe reliability is improved for jittery provider/base routes without weakening
readiness safety gates.

## Decision

This is a minimal environment-adaptation patch with controlled runtime cost and
low regression risk.
