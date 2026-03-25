# Post-Timeout Hardening Validation Report

## Objective

Validate `BL-20260324-027` after `BL-20260324-026` by running one fresh
same-origin governed candidate through:

- live Trello read-only smoke
- regenerated preview creation
- explicit approval
- real execute (`test_mode=off`)

This phase's success criterion is not a `pass` verdict. It is whether the
timeout-hardened runtime now reaches automation artifact generation and critic
review instead of failing early with read timeouts.

## Scope

In scope:

- one fresh same-origin regeneration token
- one preview candidate
- one approval
- one real execute run

Out of scope:

- git finalization
- Trello Done writeback
- additional hardening edits during validation

## Pre-Run Checks

- branch: `phase8u/validate-bl027-timeout-mitigation`
- Trello env presence confirmed from `/tmp/trello_env.sh`:
  - `TRELLO_API_KEY` set
  - `TRELLO_API_TOKEN` set
  - `TRELLO_BOARD_ID` set
- OpenAI runtime files confirmed present:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- Docker containers confirmed healthy for argus/midas sidecars and agents

## Run Summary

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260325-bl027-001`

### 1) Live Trello read-only smoke

- initial sandbox run failed with name resolution (`ConnectionError`)
- rerun with elevated network access passed (`read_count=1`)
- live smoke payload saved at:
  - `/tmp/bl027_smoke_result.json`

### 2) Regenerated inbox payload from live `mapped_preview`

- generated from smoke result `smoke_read.mapped_preview` (not fixture output)
- inbox file:
  - `inbox/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl027-001.json`
- mapped payload snapshot:
  - `/tmp/bl027_live_mapped_preview.json`

### 3) Preview ingest

Command result (`python3 skills/ingest_tasks.py --once`):

- `processed = 1`
- `rejected = 0`
- `duplicate_skipped = 0`
- `preview_created = 1`

Generated preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-4ce6c1cce934`
- preview file:
  - `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-4ce6c1cce934.json`

### 4) Approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-4ce6c1cce934.json`

### 5) Real execute (`test_mode=off`)

First attempt (non-elevated shell):

- blocked by docker environment access:
  - `Failed to initialize docker client from environment. Ensure Docker access is available or pass docker_client explicitly.`

Second attempt (elevated, explicit replay allowed):

- command included `--allow-replay`
- final sidecar:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-4ce6c1cce934.result.json`
- result:
  - `status = rejected`
  - `decision_reason = critic_verdict=needs_revision`

Worker outcomes on the successful replayed run:

- automation task:
  - `AUTO-20260325-854`
  - `status = success`
  - artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
  - output: `workspaces/automation/AUTO-20260325-854/output.json`
  - runtime: `workspaces/automation/AUTO-20260325-854/runtime.attempt-1.log`
- critic task:
  - `CRITIC-20260325-275`
  - `status = success`
  - verdict: `needs_revision`
  - artifact: `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`
  - output: `workspaces/critic/CRITIC-20260325-275/output.json`
  - runtime: `workspaces/critic/CRITIC-20260325-275/runtime.attempt-1.log`

Important runtime evidence:

- automation worker startup log shows:
  - endpoint `https://fast.vpsairobot.com/v1/chat/completions`
  - `timeout=120s`
  - `attempts=3`
- critic worker startup log shows:
  - endpoint `https://fast.vpsairobot.com/v1/chat/completions`
  - `timeout=120s`
  - `attempts=3`

## Validation Conclusion

`BL-20260324-027` objective is satisfied.

The timeout-hardened runtime now reaches automation artifact generation and
critic review on a fresh same-origin governed candidate. This is the key
blocking condition that failed in `BL-20260324-025` when the worker timed out
before artifact creation.

Remaining rejection in this run is review/business quality (`needs_revision`),
not early automation timeout failure.

## Archive Preservation

To keep audit trace and avoid losing runtime evidence, this phase archived
runtime outputs under:

- `runtime_archives/bl027/artifacts/`
- `runtime_archives/bl027/runtime/`
- `runtime_archives/bl027/state/`
- `runtime_archives/bl027/tmp/`
