# Post-Automation SSL Reliability Validation Report

## Objective

Validate `BL-20260325-038` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-038` clears SSL EOF-driven early
  automation failure under real execute

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase9b/validate-bl039-automation-transport`
- Trello env loaded from `/tmp/trello_env.sh`:
  - `TRELLO_API_KEY` set
  - `TRELLO_API_TOKEN` set
  - `TRELLO_BOARD_ID` set
- OpenAI runtime values available from:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- governed execute requires Docker worker access:
  - first sandboxed execute attempt is captured as environment evidence
  - elevated replay is used to complete governed runtime validation intent

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl039-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl039/tmp/bl039_smoke_result.json`
  - `runtime_archives/bl039/tmp/bl039_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live `smoke_read.mapped_preview` with token
  `regen-20260325-bl039-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl039-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl039-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl039/tmp/bl039_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8.result.json`
- `status = rejected`
- `decision_reason = critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-860`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- critic:
  - task `CRITIC-20260325-280`
  - `status = success`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation confirms the prior transport blocker was cleared in this run:

- automation no longer failed early with SSL EOF transport error
- runtime progressed through automation artifact generation and critic review

Current blocker shifted to generated wrapper review findings:

- critic reports success-evidence handling risk in generated wrapper semantics
  (wrapper may overstate `success` on delegate aggregate success without
  sufficiently enforcing output-write attestation contract)

Inference from this run:

- `BL-20260325-038` transport hardening achieved its intended runtime objective
  for this validation path.
- end-to-end pass is now blocked by wrapper evidence-contract semantics in the
  generated runtime artifact, not by transport instability.

## Validation Conclusion

`BL-20260325-039` is complete as a governed validation phase.

It answers the intended question after `BL-20260325-038`: SSL EOF-driven early
automation failure did not recur in this run, and execution reached critic
review. Remaining failure cause moved forward to a different blocker class
(generated wrapper evidence-contract consistency).

Next required phase: harden source-side/runtime contract guidance for generated
wrapper success-evidence semantics, then rerun fresh governed validation.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl039/artifacts/`
- `runtime_archives/bl039/runtime/`
- `runtime_archives/bl039/state/`
- `runtime_archives/bl039/tmp/`
