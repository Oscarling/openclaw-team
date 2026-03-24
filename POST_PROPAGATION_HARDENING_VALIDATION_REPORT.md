# Post-Propagation Hardening Validation Report

## Objective

Validate whether the `BL-20260324-024` hardening actually reaches a fresh
same-origin preview candidate under one governed real execute.

This phase intentionally reuses the explicit same-origin regeneration path so
the candidate can inherit the latest source-side contract without mutating the
already-completed hardening phase.

## Scope

In scope:

- one real Trello read-only smoke to confirm the target origin is still
  reachable
- one fresh same-origin preview candidate created with a new
  `regeneration_token`
- one explicit approval decision for that candidate
- one real execute run in `test_mode=off`
- one grounded comparison between:
  - the post-hardening preview contract on the fresh candidate
  - the actual governed execute result from that candidate

Out of scope:

- changing worker-runtime retry policy during this validation phase
- Git finalization
- Trello writeback / Done
- a second replay or another validation round in this phase

## Pre-Run Summary

Checked before the real run:

- reviewed `POST_PROPAGATION_RUNNER_GAP_HARDENING_REPORT.md`
- confirmed `origin` remote is present via `git remote -v`
- confirmed `/tmp/trello_env.sh` still exports working Trello credentials plus
  `TRELLO_BOARD_ID`
- confirmed OpenAI runtime values are still present in:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- confirmed this phase would stop at approval / execute and would not enter
  finalization or Trello Done

Operational note:

- `skills/trello_readonly_prep.py --output ...` still writes the fixture-mapped
  sample file by design
- for this live validation, the actual same-origin input was generated from the
  real smoke result's `mapped_preview`, then augmented with the fresh
  `regeneration_token`

## Regenerated Candidate

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260324-bl025-001`

Real Trello read-only smoke:

```bash
source /tmp/trello_env.sh && python3 skills/trello_readonly_prep.py --smoke-read --board-id "$TRELLO_BOARD_ID" --limit 1 --output /tmp/bl025_mapped.json
```

Observed result:

- read-only GET passed
- the reachable mapped card was still the intended target origin
- no Trello write operation occurred

Generated inbox payload:

- `inbox/trello-readonly-69c24cd3c1a2359ddd7a1bf8-regen-20260324-bl025-001.json`

Preview-only ingest:

```bash
python3 skills/ingest_tasks.py --once
```

Observed result:

- `processed = 1`
- `rejected = 0`
- `duplicate_skipped = 0`
- `preview_created = 1`

Generated preview candidate:

- [preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.json)

Important pre-execute checks on the new preview:

- `approved = false`
- `source.regeneration_token = regen-20260324-bl025-001`
- dedupe key is
  `origin_regeneration:trello:69c24cd3c1a2359ddd7a1bf8:regen-20260324-bl025-001`
- the automation contract profile is still
  `narrow_script_artifact_with_repo_reuse_and_reviewable_runner_contract`
- the automation description is now much richer (`length = 486`) and no longer
  truncated to `cla...`
- the automation task now includes the new hardening hints for:
  - `delegate_success_evidence`
  - `delegate_timeout`
- the critic task now declares both review artifacts:
  - `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
  - `artifacts/scripts/pdf_to_excel_ocr.py`

## Approval And Execute

Approval file written:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.json)

Approval note:

- one governed validation execute only
- no Git finalization
- no Trello Done

Execute command:

```bash
ARGUS_BASE_DIR=/Users/lingguozhong/openclaw-team \
ARGUS_APP_HOST_PATH=/Users/lingguozhong/openclaw-team \
ARGUS_SECRETS_HOST_PATH=/Users/lingguozhong/openclaw-team/secrets \
OPENAI_API_KEY="$(cat secrets/openai_api_key.txt)" \
OPENAI_API_BASE="$(cat secrets/openai_api_base.txt)" \
OPENAI_MODEL_NAME="$(cat secrets/openai_model_name.txt)" \
python3 skills/execute_approved_previews.py --once \
  --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a \
  --test-mode off
```

Observed result:

- `processed = 0`
- `rejected = 1`
- `skipped = 0`
- final decision:
  `critic_verdict=needs_revision`

Result sidecar:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.result.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a.result.json)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 1`
- `finalization = null`

Worker outputs:

- Automation task record:
  [tasks/AUTO-20260324-857.json](/Users/lingguozhong/openclaw-team/tasks/AUTO-20260324-857.json)
- Automation worker output:
  [workspaces/automation/AUTO-20260324-857/output.json](/Users/lingguozhong/openclaw-team/workspaces/automation/AUTO-20260324-857/output.json)
- Automation runtime log:
  [workspaces/automation/AUTO-20260324-857/runtime.attempt-1.log](/Users/lingguozhong/openclaw-team/workspaces/automation/AUTO-20260324-857/runtime.attempt-1.log)

No critic workspace was created for `CRITIC-20260324-278` because the automation
task failed before a reviewable artifact could be produced.

## What The Hardening Did Improve

This validation did prove that the `BL-20260324-024` hardening reached the fresh
preview candidate before execution:

- the fresh candidate preserved rich description context instead of the earlier
  truncated `cla...` form
- the new `delegate_success_evidence` and `delegate_timeout` hints are present
  on the automation task
- the critic task now carries both the wrapper and reviewed delegate script in
  its declared artifact set

So the source-side and execute-time contract hardening did propagate into the
fresh governed candidate.

## New Validation Outcome

This phase did not reach the earlier artifact-review decision point.

Instead, the automation worker failed before generating any runner artifact:

- the worker started normally
- it called the configured endpoint
  `https://fast.vpsairobot.com/v1/chat/completions`
- three consecutive LLM attempts failed with:
  `The read operation timed out`
- the automation task then closed as `failed` after `duration_ms = 183767`

This means the blocker is now different from the prior runner-review concerns.
The current blocking condition is external runtime reliability on the automation
LLM path during real execute.

## Conclusion

`BL-20260324-025` can be considered complete as a validation phase.

The fresh preview candidate clearly inherited the `BL-20260324-024` hardening,
but the governed real execute was blocked earlier by automation LLM read
timeouts before any new runner artifact could be generated or reviewed.

That makes the next step a new blocker phase, not another blind replay inside
this validation phase. The timeout behavior should be tracked separately before
attempting another governed live validation.
