# Post-Critic Snapshot Hardening Validation Report

## Objective

Validate `BL-20260325-034` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-034` removes truncation-driven
  critic rejection under real execute

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase8z/validate-bl035-critic-snapshot-hardening`
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

- `regen-20260325-bl035-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshots:
  - `runtime_archives/bl035/tmp/bl035_smoke_result.json`
  - `runtime_archives/bl035/tmp/bl035_live_mapped_preview.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live `smoke_read.mapped_preview` with token
  `regen-20260325-bl035-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl035-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl035-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8.json`

### 5) Real execute (`test_mode=off`)

First sandboxed execute:

- rejected before worker dispatch
- reason:
  `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`
- archive snapshot:
  - `runtime_archives/bl035/tmp/bl035_execute_once_sandbox.json`

Elevated replay execute (`--allow-replay`):

- final result sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8.result.json`
- `status = rejected`
- `decision_reason = critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-858`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- critic:
  - task `CRITIC-20260325-279`
  - `status = success`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 2`

## Critical Findings

This validation still ended with `critic_verdict=needs_revision`, but the
dominant blocker is no longer snapshot truncation.

Observed runtime signals:

- critic produced a detailed full-pair review across wrapper and delegate, with
  concrete findings about semantic contract alignment
- critic output did not report truncated wrapper evidence as the primary blocker
- new blocker cluster is contract semantics between wrapper and delegate:
  - zero-input handling mismatch (`partial` intent in wrapper vs `failed` in
    delegate)
  - delegate aggregate status can report `success` despite partial file outcomes
  - delegate canonical report lacks explicit output-write attestation fields

Inference from this run:

- `BL-20260325-034` appears to have addressed the truncation-driven rejection
  pattern sufficiently for critic to complete broader contract review.
- end-to-end pass is still blocked by runtime semantics in the wrapper/delegate
  contract rather than evidence-window size.

## Validation Conclusion

`BL-20260325-035` is complete as a governed validation phase.

It answers the intended question after `BL-20260325-034`: critic snapshot
completeness hardening no longer presents as the dominant runtime blocker in
this run, but the end-to-end path still fails review due remaining
wrapper/delegate semantic contract mismatches.

Next required phase: harden delegate/wrapper semantic alignment for zero-input,
aggregate status truthfulness, and explicit output-write evidence, then rerun a
fresh governed validation.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl035/artifacts/`
- `runtime_archives/bl035/runtime/`
- `runtime_archives/bl035/state/`
- `runtime_archives/bl035/tmp/`
