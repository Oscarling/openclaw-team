# Provider Arrearage Non-Retryable Runtime Report

## Context

Controlled replay now frequently fails because provider account billing state returns
`http_400` payloads containing `Arrearage` / `overdue-payment`. Those failures are
not transient network issues, so retry/fallback loops consume attempts without
changing outcome.

## Changes

- Updated `dispatcher/worker_runtime.py`:
  - Added `provider_account_arrearage` error classification using HTTP error body
    keyword detection (`Arrearage`, `overdue-payment`, `overdue payment`).
  - Marked that class as non-retryable.
  - `call_llm` now avoids auto wire-compatibility fallback/retry when this class is
    detected, because fallback condition depends on `error_class == http_400`.
- Updated `skills/execute_approved_previews.py`:
  - `_extract_llm_error_class` now returns `provider_account_arrearage` when
    Arrearage keywords are present in automation failure text.
  - Existing transient retry and auto-replay logic therefore keeps this failure
    non-retryable.

## Verification

- `python3 -m unittest -v tests/test_argus_hardening.py`
  - Added tests for arrearage classification and no-fallback runtime behavior.
- `python3 -m unittest -v tests/test_execute_approved_previews.py`
  - Added tests for arrearage class extraction and non-retry execution behavior.

All tests passed on 2026-03-29.

## Outcome

Provider account arrearage is now consistently represented as a deterministic,
non-retryable blocked condition across runtime and approval execution paths. This
reduces wasted replay attempts while preserving fail-closed control behavior.
