# Post-Contract Alignment Validation Report

## Objective

Validate `BL-20260325-028` on one fresh same-origin governed candidate by
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
- explicit recording of whether wrapper/delegate contract drift is cleared

Out of scope:

- source-code hardening inside this validation phase
- git finalization and Trello Done writeback
- additional live reruns beyond this one governed candidate

## Pre-Run Checks

- branch: `phase8w/validate-bl029-contract-alignment`
- Trello env loaded from `/tmp/trello_env.sh`:
  - `TRELLO_API_KEY` set
  - `TRELLO_API_TOKEN` set
  - `TRELLO_BOARD_ID` set
- OpenAI runtime files present:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- Docker sidecars/workers reachable for governed execute

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl029-001`

### 1) Live Trello read-only smoke

- smoke succeeded and returned `read_count=1`
- archive snapshot:
  - `runtime_archives/bl029/tmp/bl029_smoke_result.json`

### 2) Regenerated payload and preview ingest

- generated inbox payload from live mapped preview using token
  `regen-20260325-bl029-001`
- ingest result sidecar:
  - `processed/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl029-001.json.result.json`
- ingest decision:
  - `status = processed`
  - `decision = preview_created_pending_approval`
  - `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d`

### 3) Preview candidate

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d.json`

### 4) Explicit approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d.json`

### 5) Real execute (`test_mode=off`)

Final result sidecar:

- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d.result.json`
- `status = rejected`
- `decision_reason = critic_verdict=needs_revision`

Worker outcomes:

- automation:
  - task `AUTO-20260325-855`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- critic:
  - task `CRITIC-20260325-276`
  - `status = success`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

## Critical Finding

This validation did **not** clear wrapper/delegate integration drift.

The critic output and generated review identify a concrete CLI mismatch:

- wrapper command appends `--report-json <tempfile>`
  (`artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`)
- reviewed delegate `artifacts/scripts/pdf_to_excel_ocr.py` does not define
  `--report-json` in `parse_args()`

Practical impact:

- delegate can fail at argument parsing before normal conversion flow
- wrapper cannot reliably consume the expected delegate evidence handoff
- end-to-end path remains `needs_revision` despite source-side contract hints
  from `BL-20260325-028`

## Validation Conclusion

`BL-20260325-029` is complete as a governed validation phase.

It successfully answers the intended question: after `BL-20260325-028`, a fresh
same-origin governed run still exposes an integration blocker. The blocker is
now narrowed to a specific wrapper/delegate CLI contract mismatch on
`--report-json`.

Next required phase: implement and verify source-side/runtime contract alignment
for wrapper/delegate report handoff before the next governed validation run.

## Archive Preservation

To preserve runtime evidence and avoid loss from tracked artifact overwrite, this
phase archived outputs under:

- `runtime_archives/bl029/artifacts/`
- `runtime_archives/bl029/runtime/`
- `runtime_archives/bl029/state/`
- `runtime_archives/bl029/tmp/`
