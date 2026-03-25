# Post-HTTP403 Hardening Validation Report

## Objective

Validate `BL-20260325-042` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-042` changes runtime behavior for
  primary-endpoint `http_403` failures under real execute

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9e/validate-bl043-http403-hardening`
- Trello env loaded from `/tmp/trello_env.sh` with required credentials
- OpenAI runtime values loaded from `secrets/` files
- default environment had no fallback endpoint variables set
- this validation explicitly injected fallback endpoint env for execute step:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`
- governed execute requires Docker worker access:
  - first sandboxed execute attempt is captured as environment evidence
  - elevated replay is used to complete governed runtime validation intent

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl043-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl043/tmp/bl043_smoke_result.json`
  - `runtime_archives/bl043/tmp/bl043_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl043-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl043-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl043-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl043/tmp/bl043_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9.result.json`
- `status = rejected`
- decision reason includes automation terminal failure:
  - `AUTO-20260325-862`
  - `class=http_403`
  - endpoint `https://fast.vpsairobot.com/v1/chat/completions`

Worker outcomes:

- automation:
  - task `AUTO-20260325-862`
  - `status = failed`
  - no generated script artifacts were produced
  - runtime log confirms new BL-042 behavior executed:
    - attempt 1 on primary endpoint failed with `http_403`
    - one bounded auth-fallback retry was triggered
    - attempt 2 reached fallback endpoint `https://api.openai.com/v1/chat/completions`
    - fallback attempt failed with `tls_eof`
    - final attempt returned to primary and ended with `http_403`
- critic:
  - task not dispatched (`tasks/CRITIC-20260325-281.json` absent)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms BL-042 hardening behavior is active in live runtime:

- authorization failure on primary endpoint no longer hard-stops immediately
- one bounded fallback retry is actually performed when fallback endpoint is
  configured

However, end-to-end runtime still did not reach artifact generation and critic
review in this run:

- fallback endpoint call failed with `tls_eof`
- primary endpoint remained `http_403`

Inference from this run:

- `BL-20260325-042` source-side behavior change is validated as executed in
  runtime.
- blocking condition has shifted from a single-endpoint auth failure to
  multi-endpoint runtime reliability/authorization combination under real
  execute.

## Validation Conclusion

`BL-20260325-043` is complete as a governed validation phase.

It answers the intended question with runtime evidence: BL-042 authorization
fallback hardening is effective (fallback retry occurs), but this run still
cannot clear the blocker because fallback endpoint failed (`tls_eof`) and
primary remained `http_403`.

Next required phase: harden/repair multi-endpoint runtime policy or endpoint
credentials so at least one endpoint path can reach automation artifact
generation and critic dispatch under governed real execute.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl043/artifacts/`
- `runtime_archives/bl043/runtime/`
- `runtime_archives/bl043/state/`
- `runtime_archives/bl043/tmp/`
