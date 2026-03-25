# Automation Endpoint SSL Reliability Hardening Report

## Objective

Complete `BL-20260325-038` by hardening automation LLM transport handling for
runtime endpoint instability observed in `BL-20260325-037`, specifically TLS EOF
class failures.

## Scope

In scope:

- automation LLM call transport error classification hardening
- deterministic retry logging and terminal error diagnostics
- optional fallback endpoint rotation support
- focused regression coverage

Out of scope:

- fresh governed live Trello validation run
- changing external endpoint provider infrastructure
- git finalization / Trello Done writeback

## Changes

### 1) Added deterministic transport error classification

Updated `dispatcher/worker_runtime.py`:

- added `classify_llm_call_error()` to classify retry failures into stable
  classes, including:
  - `tls_eof`
  - `timeout`
  - `dns_resolution`
  - `connection_reset`
  - `connection_refused`
  - `remote_closed`
  - `http_<status>`
  - `unknown`
- mapped HTTP classes to retryability by code:
  - retryable: `408/409/425/429/500/502/503/504`
- kept unknown errors retryable to preserve existing operational resilience

### 2) Hardened call path logging and terminal error clarity

Updated `call_llm()` in `dispatcher/worker_runtime.py`:

- per-attempt warning now logs:
  - attempt index (`n/total`)
  - endpoint
  - classified error class
  - retryable flag
- retry log now includes next endpoint and delay seconds
- terminal failure now raises structured runtime error containing:
  - exhausted attempts
  - error class
  - endpoint
  - retryable state
- added `Connection: close` header to reduce stale-connection sensitivity

### 3) Added optional fallback endpoint rotation

Updated `dispatcher/worker_runtime.py`:

- added fallback URL sources:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS` (comma-separated full chat URLs)
  - `ARGUS_LLM_FALLBACK_API_BASES` (comma-separated API bases, normalized to
    `/chat/completions`)
- call attempts rotate deterministically across candidate endpoints

Updated `skills/delegate_task.py`:

- propagated fallback env into worker container runtime:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS`
  - `ARGUS_LLM_FALLBACK_API_BASES`

### 4) Added focused SSL EOF reliability regressions

Expanded `tests/test_argus_hardening.py` with:

- `test_call_llm_rotates_to_fallback_chat_url_after_retryable_tls_eof`
  - verifies first-attempt TLS EOF on primary endpoint rotates to fallback and
    succeeds
- `test_call_llm_raises_classified_tls_error_after_exhaustion`
  - verifies exhausted retries raise deterministic classified terminal error
    containing `class=tls_eof` and attempt counters

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_argus_hardening.py`
- `python3 -m unittest -v tests/test_backlog_sync.py`

## Conclusion

`BL-20260325-038` can be treated as complete as a source-side blocker-hardening
phase.

Automation transport handling now has stronger reliability semantics through:

- deterministic error classification
- endpoint-aware retry diagnostics
- configurable fallback endpoint rotation

Next required step: run a fresh same-origin governed validation to verify
whether this transport hardening allows runtime to reach artifact generation and
critic review without the prior TLS EOF blocker.
