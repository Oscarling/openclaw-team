# Provider Handshake Gemini Compat Adapter Report

## Objective

Adapt local provider handshake probing so Gemini OpenAI-compatible routes can be
validated using the same deterministic onboarding pipeline.

## Scope

In scope:

- accept Gemini API key format (`AIza...`) in probe key extraction
- auto-select payload shape by endpoint suffix:
  - `chat/completions` -> `messages`
  - `responses` -> `input`
- preserve existing fail-closed readiness rule (`2xx + api_like`)
- add probe tests for Gemini key and payload selection
- add runbook example for Gemini command path
- validate with live Desktop key4

Out of scope:

- changing non-Gemini provider credentials
- changing assess block-reason policy
- introducing model capability benchmarking

## Deliverables

- probe compatibility updates:
  - `scripts/provider_handshake_probe.py`
- tests:
  - `tests/test_provider_handshake_probe.py`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- Gemini key extraction:
  - `extract_keys` now accepts `AIza...`
- endpoint-aware payload:
  - `build_probe_payload(..., endpoint)` selects chat vs responses structure
- live run with Desktop key4:
  - probe TSV: `/tmp/provider_handshake_probe_gemini_key4_20260328.tsv`
  - assess JSON: `/tmp/provider_handshake_assessment_gemini_key4_20260328.json`
  - result: `status=ready`, `success_row_count=1`, `http_code_counts={"200":1}`

## Result

The onboarding handshake flow now supports Gemini OpenAI-compatible provider
path validation without broad architectural changes.

## Decision

This is a minimal compatibility adaptation that keeps existing safety gates
intact while expanding practical provider coverage.
