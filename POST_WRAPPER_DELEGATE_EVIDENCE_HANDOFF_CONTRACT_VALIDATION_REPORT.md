# Post-Wrapper Delegate Evidence-Handoff Contract Validation Report

## Objective

Validate `BL-20260325-058` on one fresh same-origin governed candidate by
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
- explicit recording of whether critic findings moved away from wrapper/delegate
  evidence-handoff gaps (dry-run recurrence + sidecar precedence risk)

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this governed candidate

## Pre-Run Checks

- branch: `phase9m/validate-bl059-wrapper-delegate-evidence-handoff`
- Trello env loaded from `/tmp/trello_env.sh`
- OpenAI runtime values injected from `secrets/`
- execute replay injected fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl059-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl059/tmp/bl059_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl059/tmp/bl059_smoke_elevated.json`
  - `runtime_archives/bl059/tmp/bl059_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from
  `bl059_smoke_elevated.smoke_read.mapped_preview` with token
  `regen-20260325-bl059-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-d91793a3e34b`
- archive snapshot:
  - `runtime_archives/bl059/tmp/bl059_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-d91793a3e34b`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl059-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-d91793a3e34b.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl059/tmp/bl059_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created and completed:
  - `AUTO-20260325-870`
- critic task created and completed:
  - `CRITIC-20260325-286`
- run reached critic dispatch
- final execute decision:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`
  - `critic_verdict = needs_revision`
- archive snapshots:
  - `runtime_archives/bl059/tmp/bl059_execute_once_elevated.json`
  - `runtime_archives/bl059/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl059/runtime/critic-runtime.attempt-1.log`
  - `runtime_archives/bl059/runtime/automation-output.json`
  - `runtime_archives/bl059/runtime/critic-output.json`
  - `runtime_archives/bl059/runtime/critic-produced-pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms the dominant critic findings moved away from the
`BL-20260325-058` target gaps:

- no recurrence was reported for wrapper/delegate dry-run propagation loss
- no recurrence was reported for stdout-over-sidecar evidence precedence risk

Current critic `needs_revision` focus is now:

- readonly-contract semantics ambiguity (local XLSX mutation under non-dry-run
  while summary asserts readonly flow)
- OCR runtime sufficiency/evidence strictness concerns under mixed PDF types

Inference from this run:

- `BL-20260325-058` closed the prior evidence-handoff blocker class under
  governed runtime behavior
- the next blocker class has shifted to wrapper/delegate readonly semantics and
  OCR sufficiency contract tightening

## Validation Conclusion

`BL-20260325-059` is complete as a governed validation phase.

It answers the intended question with runtime evidence: critic findings moved
away from dry-run recurrence and sidecar precedence concerns after
`BL-20260325-058`, while a new `needs_revision` blocker class remains.

## Archive Preservation

This phase archived outputs under:

- `runtime_archives/bl059/runtime/`
- `runtime_archives/bl059/state/`
- `runtime_archives/bl059/tmp/`

Note:

- `runtime_archives/bl059/state/` and `/runtime/` also retain a superseded
  first-attempt candidate (origin `trello:67f0a1b2c3d4e5f60718293a`) preserved
  for traceability after detecting mapped-output staleness relative to
  `smoke_read.mapped_preview`.
- the authoritative BL-059 outcome is the corrected same-origin candidate
  `preview-trello-69c24cd3c1a2359ddd7a1bf8-d91793a3e34b`.
