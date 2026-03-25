# Post-Semantic-Contract Alignment Validation Report

## Objective

Validate `BL-20260325-036` on one fresh same-origin governed candidate by
running:

- one live Trello read-only smoke
- one explicit same-origin regeneration
- one preview creation
- one explicit approval
- one real execute (`test_mode=off`)

This phase objective is validation truth, not forcing a `pass` verdict.

## Scope

In scope:

- one governed run against origin `trello:69c24cd3c1a2359ddd7a1bf8`
- one regeneration token and one fresh preview candidate
- runtime evidence capture for automation and critic outcomes
- explicit recording of whether `BL-20260325-036` clears the semantic
  contract blocker cluster observed in `BL-20260325-035`

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9a/validate-bl037-semantic-contract`
- Trello env loaded from `/tmp/trello_env.sh`:
  - `TRELLO_API_KEY` set
  - `TRELLO_API_TOKEN` set
  - `TRELLO_BOARD_ID` set
- OpenAI runtime values available from:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- governed execute requires Docker worker access:
  - first sandboxed execute attempt is captured as environment evidence
  - elevated replay is used to complete governed runtime validation intent

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl037-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl037/tmp/bl037_smoke_result.json`
  - `runtime_archives/bl037/tmp/bl037_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live `smoke_read.mapped_preview` with token
  `regen-20260325-bl037-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl037-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl037-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl037/tmp/bl037_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac.result.json`
- `status = rejected`
- `decision_reason` shows automation worker transport failure:
  - `AUTO-20260325-859`
  - `<urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1016)>`

Worker outcomes:

- automation:
  - task `AUTO-20260325-859`
  - `status = failed`
  - no script artifact produced
- critic:
  - not dispatched (automation failed before reviewable artifact generation)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation did **not** reach semantic-contract review closure.

The elevated governed replay was blocked by automation transport failure before
a reviewable wrapper artifact could be generated:

- three automation attempts failed with TLS/SSL EOF during endpoint call
- no automation script artifact was produced
- critic task was not dispatched

Impact:

- `BL-20260325-036` runtime effect cannot be confirmed or falsified from this
  run because execution failed earlier at worker transport reliability.

## Validation Conclusion

`BL-20260325-037` is complete as a governed validation phase.

It answers the intended runtime question with a blocker outcome: the semantic
hardening could not be validated due environment/runtime transport failure on
automation dispatch (`SSL: UNEXPECTED_EOF_WHILE_READING`), not due a new
semantic review verdict.

Next required phase: isolate and harden automation endpoint transport
reliability for governed execute, then rerun fresh same-origin validation.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl037/runtime/`
- `runtime_archives/bl037/state/`
- `runtime_archives/bl037/tmp/`
