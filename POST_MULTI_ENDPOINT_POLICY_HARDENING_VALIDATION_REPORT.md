# Post-Multi-Endpoint Policy Hardening Validation Report

## Objective

Validate `BL-20260325-044` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-044` endpoint-quarantine policy is
  active during real execute retry flow

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9f/validate-bl045-multi-endpoint-policy`
- Trello env loaded from `/tmp/trello_env.sh` with required credentials
- OpenAI runtime values loaded from `secrets/` files
- execute step injected fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`
- governed execute requires Docker worker access:
  - first sandboxed execute attempt is captured as environment evidence
  - elevated replay is used to complete governed runtime validation intent

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl045-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl045/tmp/bl045_smoke_result.json`
  - `runtime_archives/bl045/tmp/bl045_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl045-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl045-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl045-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl045/tmp/bl045_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da.result.json`
- `status = rejected`
- decision reason:
  - `critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-863`
  - `status = success`
  - script artifact generated
  - runtime log confirms endpoint-quarantine behavior was activated under auth
    failure path:
    - attempt 1 on primary endpoint `https://fast.vpsairobot.com/v1/chat/completions` failed with `timeout`
    - attempt 2 on fallback endpoint `https://api.openai.com/v1/chat/completions` failed with `http_401`
    - auth-fallback triggered and logged endpoint quarantine for the failing endpoint:
      `Quarantined endpoint for current call due to authorization failure: https://api.openai.com/v1/chat/completions`
    - attempt 3 retried on primary endpoint and succeeded
- critic:
  - task `CRITIC-20260325-281`
  - `status = success`
  - verdict: `needs_revision`
  - review artifact generated

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms BL-044 hardening behavior is active in live runtime:

- auth-fallback path now quarantines the authorization-failed endpoint for the
  remainder of the call
- runtime reached automation artifact generation and critic dispatch in this run

Compared with BL-043 blocker pattern (`primary=http_403`, `fallback=tls_eof`, no
critic dispatch), this run progressed through both workers and produced complete
runtime evidence.

Inference from this run:

- `BL-20260325-044` source-side behavior change is validated as executed in
  runtime.
- dominant blocker has shifted away from pre-critic multi-endpoint transport/auth
  termination to critic-side quality verdict (`needs_revision`).

## Validation Conclusion

`BL-20260325-045` is complete as a governed validation phase.

It answers the intended question with runtime evidence: BL-044 endpoint policy
hardening is active and the run no longer fails before artifact generation and
critic dispatch.

Next required phase: address the new critic findings surfaced after runtime
progress (wrapper/delegate success/partial evidence semantics) instead of
continuing endpoint-policy hardening in the same phase.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl045/artifacts/`
- `runtime_archives/bl045/runtime/`
- `runtime_archives/bl045/state/`
- `runtime_archives/bl045/tmp/`
