# Provider Onboarding Transient Retry Resilience Report

## Objective

Use minimal code changes to improve real-run resilience under intermittent
provider/base instability while keeping the current execution model unchanged.

## Scope

In scope:

- widen transient automation error classification for outer retry loop
- add fallback error-class extraction when `class=...` tag is absent in errors
- add regression tests for representative unstable-network signatures

Out of scope:

- provider routing redesign
- circuit-breaker state machine
- persistent health scoring

## Deliverables

- updated runtime gating script:
  - `skills/execute_approved_previews.py`
- updated tests:
  - `tests/test_execute_approved_previews.py`

## Validation Evidence

- transient class set now includes additional upstream/network classes:
  - `http_520/521/522/523` plus `tls_eof`, `dns_resolution`, and connection-
    level transient classes
- fallback parser now infers transient class from error text when explicit
  `class=...` token is missing
- new tests confirm one-time retry recovery for:
  - `HTTP Error 520` without class tag
  - TLS EOF text signature without class tag
  - DNS resolution text signature without class tag

## Result

The approval execution path now better matches real unstable provider behavior:
intermittent 52x/TLS/DNS failures are more likely to recover automatically
instead of failing closed on first outer attempt.

## Decision

This hardening improves development-stage usability for intermittent key/base
quality, but it does not convert persistently failing upstream routes into
production-stable routes.
