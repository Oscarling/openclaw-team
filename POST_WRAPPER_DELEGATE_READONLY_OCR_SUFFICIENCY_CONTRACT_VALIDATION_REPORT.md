# Post-Readonly/OCR Sufficiency Contract Validation Report

## Objective

Validate `BL-20260325-060` on one fresh same-origin governed candidate by
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
- explicit recording of whether critic findings moved away from readonly/OCR
  sufficiency contract concerns after BL-060

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this governed candidate

## Pre-Run Checks

- branch: `phase9n/validate-bl061-readonly-ocr-sufficiency-contract`
- Trello env loaded from `/tmp/trello_env.sh`
- OpenAI runtime values injected from `secrets/`
- execute replay injected fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl061-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl061/tmp/bl061_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl061/tmp/bl061_smoke_elevated.json`
  - `runtime_archives/bl061/tmp/bl061_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl061-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-0ceb21ad88dd`
- archive snapshot:
  - `runtime_archives/bl061/tmp/bl061_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-0ceb21ad88dd`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl061-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-0ceb21ad88dd.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl061/tmp/bl061_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created and completed:
  - `AUTO-20260325-871`
- critic task created and completed:
  - `CRITIC-20260325-287`
- run reached critic dispatch
- final execute decision:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`
  - `critic_verdict = needs_revision`
- archive snapshots:
  - `runtime_archives/bl061/tmp/bl061_execute_once_elevated.json`
  - `runtime_archives/bl061/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl061/runtime/critic-runtime.attempt-1.log`
  - `runtime_archives/bl061/runtime/automation-output.json`
  - `runtime_archives/bl061/runtime/critic-output.json`
  - `runtime_archives/bl061/runtime/critic-produced-pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms critic focus moved away from the BL-060 target concerns:

- no dominant finding on readonly semantics overclaim remained
- no dominant finding on OCR sufficiency gating drift remained

Current critic `needs_revision` focus is now:

- wrapper/delegate report-schema robustness and consistency across failure shapes
- insufficiently explicit propagation of delegate `error` context into wrapper
  limitations/next-step evidence

Inference from this run:

- BL-060 hardening is active and did shift reviewer focus away from readonly/OCR
  sufficiency concerns
- the next blocker class is report-schema/diagnostic contract robustness for the
  wrapper/delegate pair

## Validation Conclusion

`BL-20260325-061` is complete as a governed validation phase.

It answers the intended question with runtime evidence: critic findings moved
away from readonly/OCR sufficiency contract concerns after BL-060, while a new
`needs_revision` blocker class remains.

## Archive Preservation

This phase archived outputs under:

- `runtime_archives/bl061/runtime/`
- `runtime_archives/bl061/state/`
- `runtime_archives/bl061/tmp/`
