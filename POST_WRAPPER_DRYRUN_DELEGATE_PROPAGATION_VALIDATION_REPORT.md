# Post-Wrapper Dry-Run Delegate Propagation Validation Report

## Objective

Validate `BL-20260325-056` on one fresh same-origin governed candidate by
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
- explicit recording of whether critic findings moved away from wrapper
  dry-run propagation concerns after BL-056

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9l/validate-bl057-wrapper-dryrun-delegate-propagation`
- Trello env loaded from `/tmp/trello_env.sh` with required credentials
- OpenAI runtime values sourced from `secrets/`
- execute step injected fallback endpoint env:
  - `ARGUS_LLM_FALLBACK_CHAT_URLS=https://api.openai.com/v1/chat/completions`

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl057-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`
- archive snapshot:
  - `runtime_archives/bl057/tmp/bl057_smoke_sandbox.json`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl057/tmp/bl057_smoke_elevated.json`
  - `runtime_archives/bl057/tmp/bl057_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl057-001`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-d472aab5e3bf`
- archive snapshot:
  - `runtime_archives/bl057/tmp/bl057_ingest_once.json`

### 3) Preview candidate and approval

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-d472aab5e3bf`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl057-001`

Approval file:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-d472aab5e3bf.json`

### 4) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl057/tmp/bl057_execute_once_sandbox.json`

Elevated replay execute (`--preview-id ... --allow-replay`):

- automation task created and completed:
  - `AUTO-20260325-869`
- critic task created and completed:
  - `CRITIC-20260325-285`
- run reached critic dispatch; no pre-critic timeout exhaustion blocker
- final execute decision:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`
  - `critic_verdict = needs_revision`
- archive snapshots:
  - `runtime_archives/bl057/tmp/bl057_execute_once_elevated.json`
  - `runtime_archives/bl057/runtime/automation-runtime.attempt-1.log`
  - `runtime_archives/bl057/runtime/critic-runtime.attempt-1.log`
  - `runtime_archives/bl057/runtime/automation-output.json`
  - `runtime_archives/bl057/runtime/critic-output.json`
  - `runtime_archives/bl057/runtime/critic-produced-pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms BL-056 did not close the critic blocker under governed
runtime execution:

- runtime did progress to critic dispatch successfully
- critic verdict remained `needs_revision`
- dry-run propagation concern recurred in review findings
- an additional evidence-handoff risk was flagged:
  wrapper prefers stdout JSON scraping over explicit sidecar JSON when both are
  present

Inference from this run:

- BL-056 source merge alone is insufficient to prevent governed recurrence of
  wrapper/delegate contract issues
- dominant unresolved blocker has shifted to enforcing contract preservation for
  generated wrapper behavior (dry-run semantics + sidecar-first evidence
  handling)

## Validation Conclusion

`BL-20260325-057` is complete as a governed validation phase.

It answers the intended question with runtime evidence: critic findings did not
move away from dry-run propagation concerns after BL-056 under this governed
execute path.

Next required phase: harden wrapper/delegate evidence-handoff contract so
generated wrapper behavior consistently preserves dry-run propagation semantics
and sidecar-first report truthfulness.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite,
this phase archived outputs under:

- `runtime_archives/bl057/runtime/`
- `runtime_archives/bl057/state/`
- `runtime_archives/bl057/tmp/`
