# JSON Repair Engaged-Path Controlled Replay Report

## Objective

Complete `BL-20260326-085` by forcing a deterministic malformed-output replay
that engages JSON repair, then validate verdict/latency behavior and confirm no
output-schema contract drift.

## Scope

In scope:

- run one controlled replay where automation first receives non-JSON output
- verify repair path engagement (`json_output_repair_attempts_used > 0`)
- verify end-to-end decision quality (`processed=1`, `critic_verdict=pass`)
- archive execute/runtime/state evidence

Out of scope:

- provider production SLA evaluation
- baseline default changes

## Controlled Setup

Replay command path:

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Fixed controls:

- `ARGUS_PROVIDER_PROFILE` unset (avoid profile override)
- `OPENAI_API_BASE=http://host.docker.internal:18080/v1` (local controlled mock)
- `ARGUS_LLM_WIRE_API=chat_completions`
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`

Deterministic mock behavior:

1. automation first call -> invalid non-JSON text
2. automation repair call -> valid JSON object payload
3. critic call -> valid JSON object with `metadata.verdict=pass`

## Evidence

Primary summary:

- `runtime_archives/bl085/tmp/bl085_controlled_replay_summary.tsv`

Execute output:

- `runtime_archives/bl085/tmp/bl085_execute_replay_controlled.json`
- `runtime_archives/bl085/tmp/bl085_execute_replay_controlled.stderr.log`

Mock trace:

- `runtime_archives/bl085/tmp/bl085_mock_requests.log`

Runtime/state snapshots:

- `runtime_archives/bl085/runtime/automation-runtime.controlled.log`
- `runtime_archives/bl085/runtime/automation-output.controlled.json`
- `runtime_archives/bl085/runtime/critic-runtime.controlled.log`
- `runtime_archives/bl085/runtime/critic-output.controlled.json`
- `runtime_archives/bl085/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.controlled.json`
- `runtime_archives/bl085/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.controlled.json`

## Results

From `bl085_controlled_replay_summary.tsv` and archived outputs:

- replay status: `done`
- decision: `processed=1`, `rejected=0`
- critic verdict: `pass`
- automation status: `success`
- JSON-repair engagement: `json_output_repair_attempts_used=1`
- terminal JSON-invalid failure: `no`
- automation transient retries used: `0`
- automation wall time: `0.334s`
- critic wall time: `0.284s`

Trace consistency (`bl085_mock_requests.log`):

- `/v1/chat/completions` -> `automation_initial_invalid`
- `/v1/chat/completions` -> `automation_repair`
- `/v1/chat/completions` -> `critic_pass`

## Contract Drift Check

No schema drift observed:

- automation and critic outputs both completed with `status=success`
- required contract fields remained valid through runtime schema checks
- artifact paths/types remained under declared `artifacts/` contract

## Decision

Guidance remains unchanged:

- keep `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1` as bounded default
- keep `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1` baseline default

Rationale:

- BL-085 explicitly exercises the engaged repair path and verifies it can
  complete cleanly with pass verdict under controlled malformed-input trigger
- no evidence from this run supports raising default budgets

## Outcome

`BL-20260326-085` objective is achieved:

- engaged JSON-repair path is deterministically exercised and archived
- end-to-end decision quality under engaged path is validated (`processed/pass`)
- output-schema guarantees remain stable without contract drift
