# Single-Pass Reliability Hardening Report

## Objective

Complete `BL-20260326-078` by reducing immediate manual rerun dependence when
repo-baseline governed executes hit intermittent upstream `http_524`.

## Scope

In scope:

- source-side execute orchestration hardening for transient automation failure
- focused tests proving bounded retry behavior
- one governed replay under repo baseline profile to verify single-pass
  progression

Out of scope:

- provider-side SLA remediation
- unlimited retry policy or broad execution scheduler redesign

## Source Hardening

### 1) Bounded in-process transient automation retry

- file: `skills/execute_approved_previews.py`
- added policy:
  - detect transient automation terminal class from structured error text
  - default retry class set: `http_524`
  - retry budget env: `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS`
    - default `1`, bounded to `[0, 3]`
- behavior:
  - if first automation dispatch fails with transient class and budget remains,
    `execute_approved_previews.py` re-dispatches automation once in the same
    command run (no manual second command required)
  - sidecar and result payload now include
    `automation_transient_retries_used`

### 2) Focused regression coverage

- file: `tests/test_execute_approved_previews.py`
- added:
  - `test_process_approval_retries_once_for_http_524_then_succeeds`
  - `test_process_approval_does_not_retry_non_transient_failure`

## Validation

### Unit tests

- command:
  - `python3 -m unittest -v tests/test_execute_approved_previews.py`
- result:
  - `7/7` passed

### Governed replay (repo baseline profile)

Replay command (single invocation):

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Runtime setup:

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset (use repo-managed baseline file)
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`

Evidence:

- replay result:
  - `runtime_archives/bl078/tmp/bl078_execute_replay_singlepass.json`
- sidecar:
  - `runtime_archives/bl078/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.singlepass.json`
- worker logs/outputs:
  - `runtime_archives/bl078/runtime/automation-runtime.singlepass.log`
  - `runtime_archives/bl078/runtime/automation-output.singlepass.json`
  - `runtime_archives/bl078/runtime/critic-runtime.singlepass.log`
  - `runtime_archives/bl078/runtime/critic-output.singlepass.json`

Outcome:

- single execute command completed with:
  - `processed=1`
  - `critic_verdict=pass`
- no manual second command was required.

## Outcome

`BL-20260326-078` is complete:

- execute orchestration now has a bounded in-process recovery path for transient
  automation `http_524`
- behavior is covered by focused tests
- governed single-pass run under repo baseline profile succeeded

## Next Blocker

Queue `BL-20260326-079` to observe/tune this retry policy under repeated runs
and confirm whether default retry budget remains sufficient over time.
