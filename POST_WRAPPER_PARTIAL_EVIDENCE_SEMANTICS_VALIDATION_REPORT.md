# Post-Wrapper Partial-Evidence Semantics Validation Report

## Objective

Validate `BL-20260325-046` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-046` source-side wrapper
  success/partial semantics hardening is reflected in real execute inputs and
  resulting critic findings

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9g/validate-bl047-wrapper-partial-evidence`
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

- `regen-20260325-bl047-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl047/tmp/bl047_smoke_result.json`
  - `runtime_archives/bl047/tmp/bl047_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from elevated `smoke_read.mapped_preview` with token
  `regen-20260325-bl047-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl047-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl047-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl047/tmp/bl047_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0.result.json`
- `status = rejected`
- decision reason:
  - `critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-864`
  - `status = success`
  - script artifact generated
  - task payload confirms BL-046 hardening text is active in live runtime input:
    - includes `delegate_partial_evidence` hint
    - includes explicit constraint to keep structured partial outcomes as
      `partial` (not `failed`)
    - includes acceptance criterion requiring non-escalation of
      contract-compliant partial outcomes
- critic:
  - task `CRITIC-20260325-282`
  - `status = success`
  - verdict: `needs_revision`
  - review artifact generated
  - primary new concern reported by critic: delegate-side material status/evidence
    gap (OCR/status semantics and report richness), not wrapper
    success-vs-partial policy gap

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms BL-046 source-side hardening is active in runtime task
contract inputs.

Compared with BL-045 critic focus (wrapper success/partial semantics), BL-047
critic findings shifted to delegate-side behavior/reporting risk:

- wrapper semantic guidance is present and stronger
- dominant unresolved concern is now delegate OCR/status/report evidence quality

Inference from this run:

- `BL-20260325-046` source-side behavior change is validated as reflected in
  governed runtime inputs.
- blocker has shifted from wrapper partial-evidence contract wording to
  delegate implementation/reporting semantics.

## Validation Conclusion

`BL-20260325-047` is complete as a governed validation phase.

It answers the intended question with runtime evidence: BL-046 hardening is
active, and critic concern focus has shifted away from wrapper partial-evidence
policy to delegate-side OCR/status/report semantics.

Next required phase: harden delegate status/reporting semantics so
best-effort evidence-backed outcomes remain truthful and reviewable under real
execute without recurring critic `needs_revision` on delegate evidence quality.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl047/artifacts/`
- `runtime_archives/bl047/runtime/`
- `runtime_archives/bl047/state/`
- `runtime_archives/bl047/tmp/`
