# Post-Report-Schema Diagnostic Robustness Validation Report

## Objective

Validate `BL-20260325-062` on one fresh same-origin governed candidate by
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
- explicit recording of whether critic findings moved away from BL-062 target
  gaps (report-schema consistency and delegate-error surfacing)

Out of scope:

- source-code hardening in this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this governed candidate

## Pre-Run Checks

- branch: `phase9o/validate-bl063-report-schema-diagnostic-robustness`
- Trello env loaded from `/tmp/trello_env.sh`
- execute replay used explicit fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl063-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl063/tmp/bl063_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl063/tmp/bl063_smoke_elevated.json`
  - `runtime_archives/bl063/tmp/bl063_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl063-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-6b1d3f094609`
- archive snapshot:
  - `runtime_archives/bl063/tmp/bl063_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-6b1d3f094609`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.executed = false`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl063-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-6b1d3f094609.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl063/tmp/bl063_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created and completed:
  - `AUTO-20260325-872`
- critic task created and completed:
  - `CRITIC-20260325-288`
- run reached critic dispatch
- final execute decision:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`
  - `critic_verdict = needs_revision`
- archive snapshots:
  - `runtime_archives/bl063/tmp/bl063_execute_once_elevated.json`
  - `runtime_archives/bl063/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl063/runtime/critic-runtime.attempt-1.log`
  - `runtime_archives/bl063/runtime/automation-output.json`
  - `runtime_archives/bl063/runtime/critic-output.json`
  - `runtime_archives/bl063/runtime/critic-produced-pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 3`

## Critical Findings

This validation confirms critic focus moved away from the BL-062 target concerns:

- no dominant finding remained on sparse failure report-schema normalization
- no dominant finding remained on delegate `error` surfacing gaps

Current critic `needs_revision` focus is now:

- wrapper output-path policy is broader than tightly declared-artifact bounds
- wrapper/delegate aggregate outcome contract remains partially implicit
  (extraction-centric vs workbook-centric semantics)
- extraction-vs-export failure distinction can be surfaced more explicitly

Inference from this run:

- BL-062 hardening is active and shifted reviewer focus away from report-schema
  and delegate-error diagnostic gaps
- the next blocker class is output-boundary and aggregate outcome-contract
  clarity

## Validation Conclusion

`BL-20260325-063` is complete as a governed validation phase.

It answers the intended question with runtime evidence: critic findings moved
away from BL-062 target gaps, while a new `needs_revision` blocker class
remains.

## Archive Preservation

This phase archived outputs under:

- `runtime_archives/bl063/runtime/`
- `runtime_archives/bl063/state/`
- `runtime_archives/bl063/tmp/`
