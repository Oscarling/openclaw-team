# Fast-Provider Gateway Timeout Resilience Hardening Report

## Objective

Complete `BL-20260325-075` by hardening source/runtime behavior for persistent
fast-provider gateway timeouts and validating whether governed replay can move
past the `http_524` blocker after timeout-recovery propagation fixes.

## Scope

In scope:

- delegate env propagation fix for `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES`
- runtime timeout-recovery extension for `http_524`
- focused regressions in `tests/test_argus_hardening.py`
- one elevated governed replay under aligned profile and archived evidence

Out of scope:

- provider-side SLA remediation
- non-governed multi-provider production policy redesign

## Source Hardening

### 1) Delegate timeout-recovery propagation

- file: `skills/delegate_task.py`
- change: `build_worker_env()` now forwards
  `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES`
- effect: execute-layer override now reaches worker runtime startup path

### 2) Gateway-timeout recovery extension

- file: `dispatcher/worker_runtime.py`
- change: timeout-recovery extension now applies to error classes:
  - `timeout`
  - `http_524`
- effect: runtime can grant extra attempts for retryable Cloudflare-style
  gateway timeouts instead of stopping strictly at base retry count

### 3) Focused regressions

- file: `tests/test_argus_hardening.py`
- added/updated coverage:
  - selected provider profile keeps
    `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES` in worker env
  - `http_524` class can trigger timeout-recovery extension

## Validation Run

Replay command (governed, elevated):

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Aligned runtime profile:

- `runtime_archives/bl075/tmp/bl075_provider_profiles.json`
- `api_base=https://fast.vpsairobot.com/v1`
- `wire_api=responses`
- timeout knobs:
  - `ARGUS_LLM_TIMEOUT_SECONDS=240`
  - `ARGUS_LLM_MAX_RETRIES=2`
  - `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=2`

Primary evidence:

- replay result: `runtime_archives/bl075/tmp/bl075_execute_replay.json`
- runtime log: `runtime_archives/bl075/runtime/automation-runtime.attempt-1.log`
- worker output: `runtime_archives/bl075/runtime/automation-output.json`
- preview sidecar result:
  `runtime_archives/bl075/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.json`

## Findings

1. Timeout-recovery override propagation is fixed in live replay.
   Runtime startup log now shows:
   `timeout_recovery_retries=2`.
2. Gateway-timeout resilience extension is active.
   Runtime granted two extra attempts:
   - `attempts 2 -> 3`
   - `attempts 3 -> 4`
3. Terminal blocker remains upstream gateway timeout.
   Final outcome is still:
   `LLM call exhausted (attempts=4/4, class=http_524, endpoint=https://fast.vpsairobot.com/responses)`.

## Outcome

`BL-20260325-075` is complete as a source-hardening + governed-validation
phase:

- propagation gap is closed
- gateway-timeout recovery extension is live and validated under real execute
- dominant blocker remains persistent upstream `http_524`

## Next Blocker

Queue `BL-20260326-076`:

- mitigate persistent upstream `http_524` after BL-075 hardening
- reach automation success (and ideally critic handoff) in governed replay
