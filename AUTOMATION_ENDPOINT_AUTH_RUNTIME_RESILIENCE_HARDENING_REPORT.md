# Automation Endpoint/Auth Runtime Resilience Hardening Report

## Objective

Complete `BL-20260325-052` by hardening automation runtime endpoint/auth
resilience after `BL-20260325-051` pre-critic failures (`http_520` / `http_401`).

## Scope

In scope:

- improve LLM retry classification for transient upstream gateway failures
- preserve existing auth-fallback quarantine behavior
- add focused regressions for mixed failure sequences observed in governed runs

Out of scope:

- live governed rerun in this phase
- secrets rotation or credential provisioning changes
- Trello/read-only ingest behavior changes

## Changes

### 1) Expanded retryable HTTP classification for upstream transient failures

Updated `dispatcher/worker_runtime.py`:

- introduced `RETRYABLE_HTTP_STATUS_CODES` constant
- added transient upstream/proxy status codes to retryable set:
  - `520`, `521`, `522`, `523`, `524`
- kept existing retryable codes (`408`, `409`, `425`, `429`, `500`, `502`,
  `503`, `504`)

Effect:

- `classify_llm_call_error(...)` now treats `http_520` class failures as
  retryable instead of immediate exhaustion on first attempt.

### 2) Preserved endpoint quarantine flow for auth failures under mixed profiles

No contract-breaking behavior changes were made to auth-fallback logic itself.
With `http_520` now retryable, mixed sequences can now progress through existing
logic:

- transient upstream failure (`520`) -> retry to fallback endpoint
- fallback auth failure (`401`) -> one-time auth-fallback quarantine/retry
- retry on remaining endpoint for recovery opportunity

## Test Coverage

Updated `tests/test_argus_hardening.py` with focused regressions:

- `test_classify_llm_call_error_marks_http_520_as_retryable`
- `test_call_llm_retries_http_520_then_recovers_after_fallback_http_401`

These tests validate the targeted BL-051 failure pattern and ensure resilience
improvement is preserved.

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_argus_hardening.py` (13/13)
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-052` can be treated as complete as a source-side blocker-hardening
phase.

Automation runtime classification now gives transient `http_520` failures a
retry path, enabling endpoint rotation and auth-quarantine mechanisms to engage
before exhausting the run.

Next required step: run a fresh same-origin governed validation to confirm
runtime now reaches critic dispatch more reliably under the active endpoint/auth
profile.
