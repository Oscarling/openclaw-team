# Automation Runtime Provider Availability/Failover Iteration 1 Report

## Objective

Advance `BL-20260325-069` by improving runtime failover behavior after
`BL-068` protocol compatibility hardening, and verify whether governed execute
can reach critic handoff.

## Changes in This Iteration

Updated `dispatcher/worker_runtime.py`:

- added responses failover candidate expansion for `wire_api=auto` when
  chat endpoint returns `http_400`
- added endpoint/base compatibility helpers:
  - `endpoint_api_base(...)`
  - `response_api_base_variants(...)`
  - `compatibility_response_urls(...)`
- changed fallback behavior from single responses retry to candidate loop:
  runtime now attempts multiple responses endpoints (for example `/v1/responses`
  and `/responses`) before returning to regular retry/backoff

Updated `tests/test_argus_hardening.py`:

- added `test_call_llm_auto_fallback_tries_response_candidates_until_success`
  to verify candidate rotation recovers after first responses endpoint fails

## Validation

Local regression:

- `python3 -m unittest -v tests/test_argus_hardening.py` passed (`18/18`)

Live governed replay evidence (preview
`preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153`):

- replay A (default retries):
  - archive: `runtime_archives/bl069/tmp/bl069_execute_replay_live.json`
  - status: `rejected`
  - terminal class: `http_502`
  - terminal endpoint: `https://aixj.vip/responses`
- replay B (`ARGUS_LLM_MAX_RETRIES=6`):
  - archive: `runtime_archives/bl069/tmp/bl069_execute_replay_live_retry6.json`
  - status: `rejected`
  - terminal class: `http_502`
  - terminal endpoint: `https://aixj.vip/responses`

Runtime log evidence confirms compatibility routing is active:

- `runtime_archives/bl069/runtime/automation-runtime.retry6.log` shows
  repeated lines:
  - `Chat-completions returned http_400; retrying with responses wire API candidates (count=2).`

## Outcome

- Protocol-layer compatibility remains healthy (chat mismatch no longer terminal)
- Responses failover candidate routing is active and tested
- Dominant blocker remains upstream provider responses availability (`http_502`)
- `BL-20260325-069` is **not done yet** (critic handoff still not reached)
