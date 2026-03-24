# Automation Timeout Hardening Report

## Objective

Close `BL-20260324-026` by hardening the automation worker's LLM timeout path so
future governed live validation is no longer blocked by the previous hard-coded
60-second read timeout behavior.

This phase is a timeout-mitigation phase, not a new governed live validation.

## Root Cause Summary

`BL-20260324-025` showed a consistent pattern:

- the automation worker started normally
- the configured endpoint was
  `https://fast.vpsairobot.com/v1/chat/completions`
- each LLM call failed at roughly 60-second intervals with
  `The read operation timed out`
- the task then closed as `failed` before generating any script artifact

Code inspection confirmed the runtime cause:

- `dispatcher/worker_runtime.py` used a hard-coded
  `LLM_TIMEOUT = 60`
- the worker gave no easy runtime override for timeout / retry tuning
- startup logs did not include the effective timeout / retry configuration,
  which made real timeout debugging slower than it needed to be

## Changes

### 1. Worker runtime timeout policy

`dispatcher/worker_runtime.py` now:

- raises the default LLM read timeout from `60` to `120` seconds
- resolves timeout and retry counts through runtime helpers instead of fixed
  constants
- supports environment overrides:
  - `ARGUS_LLM_TIMEOUT_SECONDS`
  - `ARGUS_LLM_MAX_RETRIES`
- logs the effective timeout and attempt count when the worker starts

This keeps the default path more tolerant for slower real completions while
still allowing future targeted tuning without another code edit.

### 2. Environment propagation

`skills/delegate_task.py` now forwards:

- `ARGUS_LLM_TIMEOUT_SECONDS`
- `ARGUS_LLM_MAX_RETRIES`

from the host environment into the worker container when these are set.

That means future live validation can deliberately tune the runtime policy from
the outer execute command if the default mitigation still needs adjustment.

### 3. Regression coverage

Expanded `tests/test_argus_hardening.py` to cover:

- the relaxed default LLM timeout
- env-driven timeout / retry overrides for `call_llm(...)`

## Verification

Passed on 2026-03-24:

- `python3 -m unittest -v tests/test_argus_hardening.py`
- `python3 -m unittest -v tests/test_execute_approved_previews.py`

This phase still requires the normal local gate run before review and merge.

## Conclusion

`BL-20260324-026` can be treated as complete as a timeout hardening phase once
the full local gates pass and the evidence is merged.

The next correct step is a fresh governed validation phase on a new same-origin
preview candidate so the project can verify whether the new default timeout
policy is enough to let automation reach artifact generation and review under
real execution.
