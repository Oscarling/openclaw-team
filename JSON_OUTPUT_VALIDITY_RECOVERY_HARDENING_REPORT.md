# JSON Output Validity Recovery Hardening Report

## Objective

Complete `BL-20260326-083` by adding a bounded JSON-validity recovery path in
automation runtime, then validate with focused tests and governed replay
evidence.

## Scope

In scope:

- runtime hardening for non-JSON / non-object LLM outputs
- bounded repair budget with explicit fail-closed behavior
- focused regressions and one governed replay sample under fixed controls

Out of scope:

- changing default transient retry budget policy
- provider-side SLA remediation

## Implementation

Updated file:

- `dispatcher/worker_runtime.py`

Hardening details:

- added bounded JSON repair knob:
  - `ARGUS_LLM_JSON_REPAIR_ATTEMPTS` (default `1`, max `2`)
- added JSON repair path:
  - if initial LLM output cannot be parsed as a JSON object, runtime performs a
    bounded repair call through the existing LLM path using strict repair
    prompts
  - if repair succeeds, runtime continues with normalized contract flow
  - if repair fails or budget is `0`, runtime remains fail-closed with explicit
    error context
- improved observability:
  - startup log now includes `json_repair_attempts`
  - when repair is used, output metadata includes
    `json_output_repair_attempts_used`

## Focused Tests

Updated file:

- `tests/test_argus_hardening.py`

Added tests:

- `test_run_worker_repairs_invalid_json_output_once_then_succeeds`
- `test_run_worker_json_repair_budget_zero_keeps_fail_closed`

Validation command:

- `python3 -m unittest -v tests/test_argus_hardening.py tests/test_execute_approved_previews.py`

Result:

- `34/34` tests passed

## Governed Replay Evidence

Controlled replay run (BL-083 archive):

- profile controls:
  - `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
  - `ARGUS_PROVIDER_PROFILES_FILE` unset
  - `ARGUS_LLM_MAX_RETRIES=1`
  - `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
  - `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=2`
  - `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`
- command:
  - `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Summary (`runtime_archives/bl083/tmp/bl083_replay_summary.tsv`):

- `status=done`
- `processed=1`, `rejected=0`
- `critic_verdict=pass`
- `wall_seconds=131`
- `json_invalid_terminal=no`

## Evidence

- `runtime_archives/bl083/tmp/bl083_replay_summary.tsv`
- `runtime_archives/bl083/tmp/bl083_execute_replay_run01-b2.json`
- `runtime_archives/bl083/runtime/automation-runtime.run01-b2.log`
- `runtime_archives/bl083/runtime/critic-output.run01-b2.json`
- `runtime_archives/bl083/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.run01-b2.json`

## Outcome

`BL-20260326-083` objective is achieved:

- JSON-validity recovery/repair path is implemented with bounded controls
- fail-closed semantics are preserved when repair cannot recover
- focused regressions and governed replay evidence confirm improved execution
  robustness for this blocker track
