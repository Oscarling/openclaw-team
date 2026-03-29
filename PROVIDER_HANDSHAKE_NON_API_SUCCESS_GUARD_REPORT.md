# Provider Handshake Non-API Success Guard Report

## Objective

Prevent false readiness when provider routes return HTTP `200` with gateway HTML
pages instead of usable API JSON responses.

## Scope

In scope:

- add structured `api_like` signal to handshake probe TSV output
- require `2xx + api_like` for handshake success counting
- ensure assess path marks HTML/portal `200` as blocked
- add tests for false-positive suppression
- retest current Desktop backup key/base matrix with new guard

Out of scope:

- changing provider credentials
- changing upstream gateway policies
- introducing multi-step model capability probes

## Deliverables

- probe hardening:
  - `scripts/provider_handshake_probe.py`
- assess hardening:
  - `scripts/provider_handshake_assess.py`
- tests:
  - `tests/test_provider_handshake_probe.py`
  - `tests/test_provider_handshake_assess.py`

## Validation Evidence

- probe TSV now includes `api_like` column (`1/0`) for each row
- `count_success_codes` now only counts rows satisfying:
  - `http_code` in `2xx`
  - `api_like=true` (or `api_like=1`)
- assess `success_row_count` follows same rule
- assess emits `block_reason=non_api_success_payload` when `2xx` exists but no
  API-like success row
- live retest output:
  - probe: `/tmp/provider_handshake_probe_desktop_keys_20260328_v4.tsv`
  - assess: `/tmp/provider_handshake_assessment_desktop_keys_20260328_v4.json`
  - result: `status=blocked`, `success_row_count=0`, with `non_api_success_payload`

## Result

The onboarding gate now fail-closes on HTML-based `200` responses and avoids
mistaking gateway landing pages for valid model API routes.

## Decision

This is a minimal adaptation to the current provider/base environment that
improves accuracy without broad architectural changes.
