# Post-Report-Flag Realignment Validation Report

## Objective

Validate `BL-20260325-032` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-032` clears report-flag and
  discovery drift findings from `BL-20260325-031`

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase8y/validate-bl033-report-flag-realignment`
- Trello env loaded from `/tmp/trello_env.sh`:
  - `TRELLO_API_KEY` set
  - `TRELLO_API_TOKEN` set
  - `TRELLO_BOARD_ID` set
- OpenAI runtime values available from:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- Docker sidecars/workers reachable for governed execute

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl033-001`

### 1) Live Trello read-only smoke

- `status = pass`
- `read_count = 1`
- archive snapshot:
  - `runtime_archives/bl033/tmp/bl033_smoke_result.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live `smoke_read.mapped_preview` with token
  `regen-20260325-bl033-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl033-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl033-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0.json`

### 5) Real execute (`test_mode=off`)

Final result sidecar:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0.result.json`
- `status = rejected`
- `decision_reason = critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-857`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- critic:
  - task `CRITIC-20260325-278`
  - `status = partial`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

## Critical Findings

This validation still ended with `critic_verdict=needs_revision`, but the
dominant blocker changed again.

Current blocker from critic output:

- reviewed wrapper snapshot was truncated in critic evidence context, so critic
  could not fully validate syntax/completeness and returned `needs_revision`

Observations from this run:

- automation summary explicitly states wrapper uses `--report-json` handoff
- critic output did not repeat prior explicit `--report-file` mismatch finding

Inference from sources:

- `BL-20260325-032` hardening appears to have reduced the prior report-flag
  drift signal, but runtime review still fails because critic receives
  incomplete wrapper evidence for full-file validation.

## Validation Conclusion

`BL-20260325-033` is complete as a governed validation phase.

It answers the intended question after `BL-20260325-032`: the specific report
flag drift signal is no longer the main reported blocker in this run, but the
end-to-end path still fails review due truncated wrapper evidence in critic
context.

Next required phase: harden critic evidence handoff so full wrapper artifacts
can be reviewed without truncation-driven false negatives, then rerun fresh
governed validation.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl033/artifacts/`
- `runtime_archives/bl033/runtime/`
- `runtime_archives/bl033/state/`
- `runtime_archives/bl033/tmp/`
