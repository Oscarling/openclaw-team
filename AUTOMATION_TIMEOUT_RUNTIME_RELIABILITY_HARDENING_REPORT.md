# Automation Timeout Runtime Reliability Hardening Report

## Objective

Complete `BL-20260325-054` by hardening automation runtime timeout handling
after `BL-20260325-053` confirmed pre-critic exhaustion on terminal timeout
(`http_520 -> http_401 -> timeout`, exhausted at `3/3`).

## Scope

In scope:

- add a targeted timeout-resilience mechanism in runtime retry flow
- keep endpoint/auth fallback and quarantine behavior compatible with BL-052
- add focused regressions for the exact mixed failure profile from BL-053

Out of scope:

- live governed rerun in this phase
- endpoint credential provisioning or secret rotation
- Trello/read-only ingest and preview approval workflow changes

## Changes

### 1) Added configurable terminal timeout recovery retry budget

Updated `dispatcher/worker_runtime.py`:

- introduced `DEFAULT_LLM_TIMEOUT_RECOVERY_RETRIES = 1`
- added env-driven reader `llm_timeout_recovery_retries()` for
  `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES` (minimum `0`)
- added `should_grant_timeout_recovery_retry(...)` guard for:
  - `error_class == timeout`
  - retryable timeout
  - currently terminal attempt
  - remaining recovery budget > 0

Effect:

- runtime can grant one extra attempt when a retryable terminal timeout would
  otherwise exhaust immediately.

### 2) Made retry loop support bounded dynamic extension

Updated `call_llm(...)`:

- changed loop from fixed `for range(max_attempts)` to bounded `while` loop
- when terminal timeout recovery criteria are met:
  - decrement recovery budget
  - extend `max_attempts` by one
  - emit explicit runtime log line

Effect:

- preserves finite retry semantics while reducing timeout-only terminal exits in
  the observed mixed failure path.

### 3) Improved startup observability for timeout hardening settings

Updated worker startup log line to include:

- `timeout`
- `attempts`
- `timeout_recovery_retries`

Effect:

- governed runtime logs can now directly show whether timeout-recovery budget
  was active during a run.

## Test Coverage

Updated `tests/test_argus_hardening.py` with focused regressions:

- `test_call_llm_grants_terminal_timeout_recovery_retry_after_auth_quarantine`
- `test_call_llm_can_disable_timeout_recovery_retry`

Coverage intent:

- validate default resilience path for BL-053-like sequence
  (`520 -> 401 -> timeout -> recovery`)
- validate explicit opt-out keeps old terminal behavior
  (`ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0` -> `attempts=3/3` timeout exhaustion)

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_argus_hardening.py` (15/15)
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-054` is complete as a source-side timeout/runtime reliability
hardening phase.

The automation runtime now has a bounded, configurable timeout recovery path
that directly addresses the BL-053 terminal timeout blocker while retaining
finite retries and existing endpoint/auth quarantine logic.

Next required step: run one fresh same-origin governed validation to verify
this hardening improves real execute progression to critic dispatch under live
conditions.
