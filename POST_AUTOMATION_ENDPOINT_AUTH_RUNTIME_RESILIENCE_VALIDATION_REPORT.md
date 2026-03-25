# Post-Automation Endpoint/Auth Runtime Resilience Validation Report

## Objective

Validate `BL-20260325-052` on one fresh same-origin governed candidate by
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
- runtime evidence capture for automation/critic progression
- explicit recording of whether `BL-20260325-052` endpoint/auth hardening
  improves progression beyond pre-critic blockers

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9j/validate-bl053-automation-endpoint-auth-resilience`
- Trello env loaded from `/tmp/trello_env.sh` with required credentials
- OpenAI runtime values sourced from `secrets/`
- execute step injected fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl053-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl053/tmp/bl053_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl053/tmp/bl053_smoke_result.json`
  - `runtime_archives/bl053/tmp/bl053_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl053-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a`
- archive snapshot:
  - `runtime_archives/bl053/tmp/bl053_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl053-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl053/tmp/bl053_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created: `AUTO-20260325-867`
- runtime log confirms BL-052 hardening behavior was active:
  - attempt 1: `http_520` on primary endpoint classified as retryable
  - attempt 2: rotated to fallback endpoint, encountered `http_401`, applied
    auth-fallback quarantine
  - attempt 3: retried remaining primary endpoint
- final outcome remained rejected before critic dispatch due terminal timeout:
  - `LLM call exhausted (attempts=3/3, class=timeout, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True)`
- archive snapshots:
  - `runtime_archives/bl053/tmp/bl053_execute_once_elevated.json`
  - `runtime_archives/bl053/runtime/automation-runtime.attempt-1.log`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`
- no critic task artifact produced in this phase (`CRITIC-20260325-284` not
  materialized)

## Critical Findings

This validation confirms BL-052 hardening is active in real runtime:

- `http_520` no longer causes immediate first-attempt exhaustion
- runtime progressed through endpoint rotation and auth-quarantine logic exactly
  as intended by BL-052

However, this run still did not reach critic dispatch because the final primary
attempt timed out.

Inference from this run:

- BL-052 endpoint/auth resilience hardening is validated as executed
- dominant unresolved blocker has shifted from `http_520` classification failure
  to timeout reliability on the remaining endpoint after fallback quarantine

## Validation Conclusion

`BL-20260325-053` is complete as a governed validation phase.

It answers the intended question with runtime evidence: BL-052 behavior is
active and improves progression through mixed endpoint/auth failures, but the
run still ends pre-critic due timeout reliability limits on the primary
endpoint.

Next required phase: harden automation timeout/runtime reliability so governed
execute can consistently reach critic dispatch after endpoint/auth recovery.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl053/runtime/`
- `runtime_archives/bl053/state/`
- `runtime_archives/bl053/tmp/`
