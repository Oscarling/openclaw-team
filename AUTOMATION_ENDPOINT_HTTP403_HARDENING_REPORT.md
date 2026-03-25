# Automation Endpoint HTTP 403 Hardening Report

## Objective

Complete `BL-20260325-042` by hardening automation LLM endpoint behavior so a
primary-endpoint authorization failure (`HTTP 401/403`) can perform one
controlled fallback-endpoint retry when fallback endpoints are configured,
instead of terminating immediately before artifact generation.

## Scope

In scope:

- adjust worker-runtime retry policy for authorization failures under
  multi-endpoint configuration
- preserve non-retry behavior for HTTP 401/403 when no fallback endpoint exists
- focused regression coverage for the new authorization-fallback behavior

Out of scope:

- live governed runtime validation rerun
- endpoint credential rotation or external secret changes
- critic-side contract changes

## Changes

### 1) Added explicit auth-fallback retry gate

Updated `dispatcher/worker_runtime.py`:

- added helper `should_retry_auth_failure_on_fallback(...)` to permit retry only
  when all of the following are true:
  - error class is `http_401` or `http_403`
  - at least one remaining retry attempt exists
  - there is a distinct fallback endpoint candidate
- in `call_llm(...)`, added one-time authorization fallback retry state so
  endpoint-authorization fallback is explicit and bounded
- logging now reflects the effective retryability decision and emits a clear
  info log when auth-fallback retry is activated

Result: authorization failure on the primary endpoint can now move to a
configured fallback endpoint once, while keeping behavior deterministic.

### 2) Added focused regression tests

Updated `tests/test_argus_hardening.py`:

- `test_call_llm_rotates_to_fallback_chat_url_after_http_403_on_primary`
  verifies primary `HTTP 403` now rotates to fallback endpoint and succeeds
- `test_call_llm_http_403_without_fallback_remains_non_retryable`
  verifies no fallback still fails immediately on first `HTTP 403`

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_argus_hardening.py`

## Conclusion

`BL-20260325-042` can be treated as complete as a source-side blocker-hardening
phase.

Automation runtime now has deterministic, bounded authorization-fallback behavior
for endpoint-specific `HTTP 401/403` failures when fallback endpoints are
configured. Live effectiveness still requires fresh governed validation.

Next required step: run a fresh same-origin governed validation to verify
whether this hardening restores automation artifact generation and critic
execution under real runtime conditions.
