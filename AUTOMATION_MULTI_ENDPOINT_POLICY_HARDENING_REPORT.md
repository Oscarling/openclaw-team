# Automation Multi-Endpoint Policy Hardening Report

## Objective

Complete `BL-20260325-044` by hardening automation multi-endpoint retry
behavior for the mixed failure pattern confirmed in `BL-20260325-043`:

- primary endpoint fails authorization (`http_403`)
- fallback endpoint fails transport (`tls_eof`)
- retry rotation can return to the known-auth-failed primary endpoint within the
  same call, re-triggering a terminal `http_403` before critic dispatch

This phase targets deterministic source-side policy hardening, not live runtime
closure.

## Scope

In scope:

- harden endpoint selection policy in `call_llm(...)` for the specific
  auth-fallback path
- keep retries bounded and behavior deterministic
- add focused regression coverage for mixed auth/transport sequence

Out of scope:

- live governed execute rerun
- endpoint credential rotation
- infrastructure/network remediations external to repository code

## Changes

### 1) Added per-call endpoint quarantine after auth-fallback trigger

Updated `dispatcher/worker_runtime.py`:

- added helper `remove_endpoint_for_current_call(chat_urls, blocked_url)`
- when a primary endpoint `http_401/http_403` activates the one-time
  auth-fallback retry, the failed endpoint is removed from candidate rotation
  for the remainder of the current call
- emitted explicit log line:
  - `Quarantined endpoint for current call due to authorization failure: <url>`

Result:

- current call no longer rotates back to a known-authorized-failed endpoint
  after fallback transport retry
- endpoint order stays deterministic and bounded inside the same retry budget

### 2) Added focused mixed-failure regression coverage

Updated `tests/test_argus_hardening.py`:

- added
  `test_call_llm_quarantines_primary_after_http_403_and_retries_fallback`
- asserts call order under mixed failures with `max_retries=3` is:
  - primary (`http_403`)
  - fallback (`tls_eof`)
  - fallback (success)
- verifies timeout stability and successful structured response return

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_argus_hardening.py`

## Conclusion

`BL-20260325-044` can be treated as complete as a source-side blocker-hardening
phase.

Automation runtime now quarantines authorization-failed primary endpoints for
the remainder of a call once auth-fallback is triggered, preventing immediate
re-entry into known-403 endpoints during the same retry cycle.

Next required step: run a fresh same-origin governed validation to confirm this
policy change improves end-to-end live execute progression to artifact
generation and critic dispatch.
