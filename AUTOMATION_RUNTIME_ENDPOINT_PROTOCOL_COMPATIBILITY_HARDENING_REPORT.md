# Automation Runtime Endpoint/Protocol Compatibility Hardening Report

## Objective

Close `BL-20260325-068` by hardening automation runtime provider
compatibility after `BL-20260325-067` findings:

- avoid terminal `http_400` contract mismatch when provider expects
  responses-style API
- support explicit wire-api selection and automatic compatibility fallback
- preserve existing retry/failover behavior and add focused regression tests

## Scope

In scope:

- `dispatcher/worker_runtime.py` LLM endpoint/protocol compatibility hardening
- `skills/delegate_task.py` runtime env propagation for wire-api config
- focused regressions in `tests/test_argus_hardening.py`
- one real replay check against configured provider endpoint

Out of scope:

- upstream provider availability/SLA remediation
- critic-level semantic quality improvements
- Trello workflow redesign

## Changes

### 1) Runtime now supports wire-api modes (`chat_completions` / `responses` / `auto`)

Updated `dispatcher/worker_runtime.py`:

- added wire-api normalization and endpoint builders:
  - `normalize_wire_api(...)`
  - `normalize_chat_endpoint(...)`
  - `normalize_responses_endpoint(...)`
- `get_llm_settings()` now resolves and carries:
  - `wire_api`
  - `chat_url`
  - `responses_url`
  - `endpoint_url` (active primary endpoint)
- startup runtime log now records endpoint plus `wire_api`

Effect:

- worker can be explicitly configured for responses protocol or run in
  compatibility auto mode.

### 2) `call_llm(...)` adds compatibility fallback from chat `http_400` to responses endpoint

Updated `dispatcher/worker_runtime.py`:

- refactored request path with protocol-specific helpers:
  - `build_chat_payload(...)`
  - `build_responses_payload(...)`
  - `extract_content_from_chat_result(...)`
  - `extract_content_from_responses_result(...)`
  - `call_llm_once(...)`
- in `wire_api=auto`, if chat-completions returns `http_400`, runtime retries
  once immediately against the corresponding `/responses` endpoint before
  regular backoff cycle
- kept existing retry classification/backoff/auth-fallback logic intact

Effect:

- terminal failure class moved away from protocol mismatch (`http_400`) and
  progressed into provider runtime availability class (`http_502`), which is a
  different blocker.

### 3) Delegate path now propagates wire-api environment controls

Updated `skills/delegate_task.py`:

- `build_worker_env(...)` now forwards:
  - `ARGUS_LLM_WIRE_API` (and aliases `OPENAI_WIRE_API` / `WIRE_API`)
  - `ARGUS_LLM_FALLBACK_RESPONSE_URLS`

Effect:

- runtime protocol selection/fallback config can be controlled at execute
  time without container image rebuild.

## Tests

Updated tests in `tests/test_argus_hardening.py`:

- `test_call_llm_auto_falls_back_to_responses_after_http_400`
- `test_get_llm_settings_supports_responses_wire_api`

Validation runs:

- `python3 -m unittest -v tests/test_argus_hardening.py`
  - passed (`17/17`)
- `python3 scripts/backlog_lint.py`
  - passed
- `python3 scripts/backlog_sync.py`
  - passed

## Real Replay Evidence

Executed one real replay with current provider env (`/tmp/trello_env.sh`):

- command:
  - `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`
- archive:
  - `runtime_archives/bl068/tmp/bl068_execute_replay_live.json`
  - `runtime_archives/bl068/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl068/runtime/automation-output.json`

Observed runtime progression:

- chat endpoint still returns `http_400`
- runtime auto-fallback switches to responses endpoint
- terminal failure is now `http_502` at `https://aixj.vip/v1/responses`

This confirms protocol mismatch hardening is active; current dominant blocker
is upstream/runtime availability, not request contract mismatch.

## Outcome

`BL-20260325-068` source-side hardening is complete:

- automation runtime now has explicit wire-api compatibility controls
- automatic chat->responses fallback prevents terminal `http_400` contract
  mismatch in this provider path
- next blocker class is provider responses-endpoint availability/failover
  reliability (`http_502`)
