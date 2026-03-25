# Post-Wrapper Success-Evidence Validation Report

## Objective

Validate `BL-20260325-040` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-040` clears wrapper
  success-evidence blocker findings under real execute

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9c/validate-bl041-wrapper-success-evidence`
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

- `regen-20260325-bl041-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl041/tmp/bl041_smoke_result.json`
  - `runtime_archives/bl041/tmp/bl041_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl041-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl041-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl041-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl041/tmp/bl041_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7.result.json`
- `status = rejected`
- decision reason includes automation terminal failure:
  - `AUTO-20260325-861`
  - `class=http_403`
  - endpoint `https://fast.vpsairobot.com/v1/chat/completions`

Worker outcomes:

- automation:
  - task `AUTO-20260325-861`
  - `status = failed`
  - no generated script artifacts were produced
- critic:
  - task not dispatched (`tasks/CRITIC-20260325-281.json` absent)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation did not reach wrapper-review evaluation.

- `BL-20260325-040` source-side contract hardening propagated into the fresh
  preview candidate inputs/constraints.
- real execute replay failed earlier at automation endpoint authorization
  (`HTTP 403: Forbidden`), so no new runner artifact was generated and critic
  review was never dispatched.

Inference from this run:

- the runtime question for `BL-20260325-040` remains unclosed in live evidence
  because execution terminated before wrapper/critic evaluation.
- the active blocker has shifted to automation endpoint authorization/runtime
  access (`http_403`) under governed real execute.

## Validation Conclusion

`BL-20260325-041` is complete as a governed validation phase.

It answers the intended question truthfully: this run could not yet validate
whether BL-040 clears wrapper success-evidence review findings, because runtime
failed earlier with automation `HTTP 403` and never reached critic artifact
review.

Next required phase: harden or repair automation endpoint authorization/runtime
access so a fresh governed run can reach automation artifact generation and
critic review again.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl041/artifacts/`
- `runtime_archives/bl041/runtime/`
- `runtime_archives/bl041/state/`
- `runtime_archives/bl041/tmp/`
