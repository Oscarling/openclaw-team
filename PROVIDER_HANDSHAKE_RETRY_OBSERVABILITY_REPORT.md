# Provider Handshake Retry Observability Report

## Objective

Expose structured retry metrics in handshake outputs so operators can quickly
distinguish network jitter from auth/policy blocking.

## Scope

In scope:

- add `retry_count` and `retry_reasons` to probe TSV output
- keep retry policy unchanged (bounded retry only for retryable transport/5xx)
- add retry aggregate metrics to assess summary:
  - `retry_attempt_total`
  - `rows_with_retry`
  - `retry_reason_counts`
- add unit coverage for observability fields
- document fields in local runbook

Out of scope:

- changing readiness decision rules
- changing provider credentials or route policies
- adding new external dependencies

## Deliverables

- probe update:
  - `scripts/provider_handshake_probe.py`
- assess update:
  - `scripts/provider_handshake_assess.py`
- tests:
  - `tests/test_provider_handshake_probe.py`
  - `tests/test_provider_handshake_assess.py`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- probe TSV header now includes:
  - `api_like`
  - `retry_count`
  - `retry_reasons`
- retry reasons are normalized to low-cardinality classes
- assess summary now reports retry totals and reason counts
- unit tests verify:
  - retry observability on transport timeout and 5xx retry flows
  - non-retry behavior for auth failures (`401`)
  - retry aggregation in assess summary

## Result

Handshake diagnostics are now easier to interpret during unstable provider/base
conditions, with no change to fail-closed readiness semantics.

## Decision

This is a minimal, low-risk observability hardening step aligned with the
current local-first blocked-provider workflow.
