# Post-Output-Boundary + Outcome-Contract Validation Report

## Objective

Validate `BL-20260325-064` on one fresh same-origin governed candidate by
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
- explicit recording of whether critic findings moved away from BL-064 target
  gaps (output-boundary policy and extraction-vs-export outcome-contract
  clarity)

Out of scope:

- source-code hardening in this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this governed candidate

## Pre-Run Checks

- branch: `phase9p/validate-bl065-output-boundary-outcome-contract`
- Trello env loaded from `/tmp/trello_env.sh`
- execute replay used explicit OpenAI env injection with fallback chat endpoint

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl065-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl065/tmp/bl065_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl065/tmp/bl065_smoke_elevated.json`
  - `runtime_archives/bl065/tmp/bl065_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl065-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-994e5ccbfd0b`
- archive snapshot:
  - `runtime_archives/bl065/tmp/bl065_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-994e5ccbfd0b`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.executed = false`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl065-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-994e5ccbfd0b.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl065/tmp/bl065_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created and completed:
  - `AUTO-20260325-873`
- critic task created and completed:
  - `CRITIC-20260325-289`
- run reached critic dispatch
- final execute decision:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`
  - `critic_verdict = needs_revision`
- archive snapshots:
  - `runtime_archives/bl065/tmp/bl065_execute_once_elevated.json`
  - `runtime_archives/bl065/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl065/runtime/critic-runtime.attempt-1.log`
  - `runtime_archives/bl065/runtime/automation-output.json`
  - `runtime_archives/bl065/runtime/critic-output.json`
  - `runtime_archives/bl065/runtime/critic-produced-pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms critic focus moved away from BL-064 target concerns:

- no dominant finding remained on wrapper output-boundary policy
- extraction-vs-export phase diagnostics remained available and were not the
  primary blocker class

Current critic `needs_revision` focus is now:

- wrapper/delegate subprocess outcome contract is still inconsistent:
  - wrapper does not treat delegate non-zero exit code with JSON evidence as a
    hard failure signal
  - wrapper/delegate no-input and partial semantics are not fully canonicalized
- runtime diagnostics completeness is still weak:
  - stderr/stdout preservation in structured wrapper evidence is incomplete

Inference from this run:

- BL-064 hardening is active and shifted reviewer focus away from
  output-boundary enforcement
- next blocker class is wrapper/delegate execution outcome-contract strictness
  plus diagnostic completeness

## Validation Conclusion

`BL-20260325-065` is complete as a governed validation phase.

It answers the intended question with runtime evidence: critic findings moved
away from BL-064 target output-boundary concerns, while a new
`needs_revision` blocker class remains around execution outcome-contract
strictness and diagnostic completeness.

## Archive Preservation

This phase archived outputs under:

- `runtime_archives/bl065/runtime/`
- `runtime_archives/bl065/state/`
- `runtime_archives/bl065/tmp/`
