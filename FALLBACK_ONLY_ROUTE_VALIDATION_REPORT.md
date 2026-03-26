# Fallback-Only Route Validation Report

## Objective

Execute the first controlled validation for `BL-20260326-096`: verify whether
removing the `aixj` primary path and using fallback-only provider endpoints can
recover real automation execution.

## Scope

In scope:

- run governed replay on fallback-only profile
- keep existing execution contract and rollback discipline
- archive execute/runtime/state evidence under `runtime_archives/bl096/`

Out of scope:

- full 4-sample promotion canary
- provider infrastructure change

## Controlled Setup

Profile (`runtime_archives/bl096/tmp/provider_profiles.bl096.json`):

- `api_base=https://fast.vpsairobot.com/v1`
- `wire_api=responses`
- fallback responses URL: `https://fast.vpsairobot.com/responses`
- key source: Desktop backup key (`OPENAI_API_KEY_BL096`)
- model: `gpt-5-codex`

Runtime controls:

- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS=1`
- prompt compaction: `ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS=1200`

## Evidence

Primary replay artifacts:

- `runtime_archives/bl096/tmp/bl096_execute_s01.gpt-5-codex.json`
- `runtime_archives/bl096/runtime/automation-runtime.s01.gpt-5-codex.log`
- `runtime_archives/bl096/runtime/automation-output.s01.gpt-5-codex.json`
- `runtime_archives/bl096/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.s01.gpt-5-codex.json`

## Result

Replay `s01` outcome:

- `status=rejected`
- `processed=0`, `rejected=1`
- terminal automation failure chain remained endpoint-side:
  - attempt 1: `timeout` on `https://fast.vpsairobot.com/v1/responses`
  - attempt 2: `http_502` on `https://fast.vpsairobot.com/responses`
  - attempt 3: `tls_eof` on `https://fast.vpsairobot.com/v1/responses`

## Decision

`BL-20260326-096` is **not cleared**.

Current status:

- fallback-only route did not recover stable real execution
- endpoint-chain instability remains the dominant blocker under governed replay

Next blocker candidate:

- `BL-20260326-097`: establish a new stable provider/endpoint route (or
  equivalent external topology change) before retrying canary clearance.
