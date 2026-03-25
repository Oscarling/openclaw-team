# Post-CLI Alignment Validation Report

## Objective

Validate `BL-20260325-030` on one fresh same-origin governed candidate by
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
- explicit recording of whether `BL-20260325-030` clears the report-handoff
  blocker in real execution

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase8x/validate-bl031-cli-alignment`
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

- `regen-20260325-bl031-001`

### 1) Live Trello read-only smoke

First sandboxed read:

- blocked by DNS / sandbox network policy
- error: `ConnectionError` / `NameResolutionError`

Elevated rerun:

- `status = pass`
- `read_count = 1`
- archive snapshot:
  - `runtime_archives/bl031/tmp/bl031_smoke_result.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live `smoke_read.mapped_preview` with token
  `regen-20260325-bl031-001`
- inbox file:
  - `inbox/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl031-001.json`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl031-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3.json`

Pre-execute state:

- `approved = false`
- `execution.status = pending_approval`
- `execution.attempts = 0`
- `source.regeneration_token = regen-20260325-bl031-001`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3.json`

### 5) Real execute (`test_mode=off`)

Final result sidecar:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3.result.json`
- `status = rejected`
- `decision_reason = critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-856`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- critic:
  - task `CRITIC-20260325-277`
  - `status = partial`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

## Critical Findings

This validation did **not** clear integration-level report-handoff drift.

The critic output and generated review identify a new concrete CLI mismatch on
the same boundary:

- generated wrapper invokes delegate with `--report-file`
- reviewed delegate `artifacts/scripts/pdf_to_excel_ocr.py` defines
  `--report-json` (not `--report-file`)

Practical impact:

- wrapper/delegate pair remains contract-incompatible on report sidecar
  handoff
- end-to-end execution remains `critic_verdict=needs_revision`

Additional review concerns in this run:

- wrapper snapshot reviewed by critic was truncated
- wrapper preflight PDF discovery (`iterdir`) diverges from delegate recursive
  discovery (`rglob`)

## Validation Conclusion

`BL-20260325-031` is complete as a governed validation phase.

It answers the intended question after `BL-20260325-030`: the prior
delegate-side `--report-json` addition alone is insufficient. The active
blocker shifted to generated wrapper behavior (`--report-file`), and report
handoff contract alignment is still not closed end-to-end.

Next required phase: source-side/runtime contract hardening that forces wrapper
invocation to use the reviewed delegate CLI contract, then another fresh
governed validation run.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl031/artifacts/`
- `runtime_archives/bl031/runtime/`
- `runtime_archives/bl031/state/`
- `runtime_archives/bl031/tmp/`
