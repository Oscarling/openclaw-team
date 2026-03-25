# Post-Wrapper Provenance/Path Traceability Validation Report

## Objective

Validate `BL-20260325-050` on one fresh same-origin governed candidate by
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
- runtime evidence capture for automation and critic progression
- explicit recording of whether `BL-20260325-050` wrapper provenance/path
  traceability hardening can be evaluated under real execute

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9i/validate-bl051-wrapper-provenance-traceability`
- Trello env loaded from `/tmp/trello_env.sh` with required credentials
- governed execute requires Docker worker access:
  - first sandboxed execute attempt captured as environment evidence
  - elevated replays used to pursue real runtime evidence

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl051-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl051/tmp/bl051_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl051/tmp/bl051_smoke_result.json`
  - `runtime_archives/bl051/tmp/bl051_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl051-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-58e83a71aacc`
- archive snapshot:
  - `runtime_archives/bl051/tmp/bl051_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-58e83a71aacc`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl051-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-58e83a71aacc.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl051/tmp/bl051_execute_once_sandbox.json`

Elevated replay attempt A (secrets-sourced primary endpoint):

- automation task created: `AUTO-20260325-866`
- result: automation failed before critic dispatch
- reason:
  `LLM call exhausted ... class=http_520 ... endpoint=https://fast.vpsairobot.com/v1/chat/completions`
- archive snapshot:
  - `runtime_archives/bl051/tmp/bl051_execute_once_elevated.json`

Elevated replay attempt B (controlled primary override to OpenAI):

- same automation task id replayed
- result: automation failed before critic dispatch
- reason:
  `LLM call exhausted ... class=http_401 ... endpoint=https://api.openai.com/v1/chat/completions`
- archive snapshot:
  - `runtime_archives/bl051/tmp/bl051_execute_once_elevated_openai_primary.json`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 3`
- no critic task artifact produced in this phase (`CRITIC-20260325-284` was not
  materialized)

## Critical Findings

This governed validation reached real automation execution but failed before
critic dispatch due runtime endpoint/auth blockers:

- attempt A blocked by upstream `http_520` on the configured primary endpoint
- attempt B blocked by `http_401` when forcing OpenAI primary endpoint

As a result, this phase could not produce critic evidence to directly confirm
whether BL-050 wrapper provenance/path traceability hardening shifts critic
findings under real execute.

Inference from this run:

- wrapper hardening from BL-050 remains source-complete, but runtime validation
  is currently blocked by automation endpoint/auth reliability conditions.

## Validation Conclusion

`BL-20260325-051` is complete as a governed validation phase, but the validation
result is **inconclusive on critic-shift outcome** due pre-critic automation
runtime failures (`http_520` / `http_401`).

Next required phase: harden automation endpoint/auth runtime behavior so
governed execute can reliably reach critic dispatch and evaluate wrapper-level
critic findings.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl051/runtime/`
- `runtime_archives/bl051/state/`
- `runtime_archives/bl051/tmp/`
