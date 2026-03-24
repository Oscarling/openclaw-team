# Hardened Preview Validation Report

## Objective

Validate whether the hardened preview artifact contract from
`BL-20260324-018` actually clears the prior review findings when exercised on a
fresh preview candidate.

This phase intentionally uses the new explicit same-origin regeneration path
from `BL-20260324-020` instead of creating a fresh Trello card.

## Scope

In scope:

- one real Trello read-only smoke to confirm the target card is still reachable
- one regenerated same-origin preview candidate with an explicit
  `regeneration_token`
- one explicit approval decision for that candidate
- one real execute run in `test_mode=off`
- one grounded comparison between:
  - the prior `BL-20260324-017` findings
  - the new `BL-20260324-019` outcome

Out of scope:

- changing `skills/execute_approved_previews.py`
- git finalization
- Trello writeback / Done
- a second replay or another validation round in this phase

## Pre-Run Summary

Checked before the real run:

- reviewed `PROJECT_CHAT_AND_WORK_LOG.md`
- reviewed `BASELINE_FREEZE_NOTE.md`
- confirmed `origin` remote is present via `git remote -v`
- confirmed Trello credentials are available via `/tmp/trello_env.sh`
- confirmed OpenAI runtime values are available from:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- confirmed this phase would stop at approval / execute and would not enter
  finalization or Trello Done

## Regenerated Candidate

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260324-bl019-001`

Real Trello read-only smoke:

```bash
source /tmp/trello_env.sh && python3 skills/trello_readonly_prep.py --smoke-read --board-id "$TRELLO_BOARD_ID" --limit 1
```

Observed result:

- read-only GET passed
- the reachable mapped card was the intended target origin
- no Trello write operation occurred

Generated inbox payload:

- `inbox/trello-readonly-69c24cd3c1a2359ddd7a1bf8-regen-20260324-bl019-001.json`

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

- [preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.json)

Important pre-execute checks on the new preview:

- `approved = false`
- `source.regeneration_token = regen-20260324-bl019-001`
- dedupe key is
  `origin_regeneration:trello:69c24cd3c1a2359ddd7a1bf8:regen-20260324-bl019-001`
- automation contract profile is
  `narrow_script_artifact_with_repo_reuse_and_format_fidelity`
- the automation task now includes:
  - `preferred_base_script = artifacts/scripts/pdf_to_excel_ocr.py`
  - `reference_docs`
  - `.xlsx` fidelity guidance
  - path-portability guidance
  - runtime-summary guidance

## Approval And Execute

Approval file written:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.json)

Approval note:

- one governed validation execute only
- no git finalization
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
  --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36 \
  --test-mode off
```

Observed result:

- `processed = 0`
- `rejected = 1`
- `skipped = 0`
- final decision:
  `critic_verdict=needs_revision`

Result sidecar:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.result.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36.result.json)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 1`
- `finalization = null`

Worker outputs:

- Automation:
  [workspaces/automation/AUTO-20260324-855/output.json](/Users/lingguozhong/openclaw-team/workspaces/automation/AUTO-20260324-855/output.json)
- Critic:
  [workspaces/critic/CRITIC-20260324-276/output.json](/Users/lingguozhong/openclaw-team/workspaces/critic/CRITIC-20260324-276/output.json)
- Review artifact:
  [artifacts/reviews/pdf_to_excel_ocr_inbox_review.md](/Users/lingguozhong/openclaw-team/artifacts/reviews/pdf_to_excel_ocr_inbox_review.md)
- Generated script artifact:
  [artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py](/Users/lingguozhong/openclaw-team/artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py)

## Comparison Against The Prior Findings

The prior `BL-20260324-017` execute exposed four artifact-quality concerns.

### 1. Fake `.xlsx` output semantics

Prior problem:

- the generated script wrote non-XLSX content to a `.xlsx` path

New result:

- cleared for this validation target
- the new generated runner wraps the repository base script instead of
  fabricating a new converter
- the critic review no longer flags fake `.xlsx` semantics as a primary issue

### 2. Hardcoded input path

Prior problem:

- the generated script hardcoded an unrelated local input path

New result:

- cleared for this validation target
- the new runner takes `--input-dir` and uses the provided parameter
- the critic review does not flag hardcoded-path behavior

### 3. Collapsed description context

Prior problem:

- the automation description collapsed to a heading fragment such as `Purpose:`

New result:

- materially improved and sufficient to treat the original finding as cleared
- the condensed description is still shortened with `...`, but it now preserves
  meaningful execution context instead of collapsing to a bare heading fragment
- the critic review does not flag traceability collapse

### 4. Missing runtime evidence expectations

Prior problem:

- the review contract lacked stronger guidance about runtime-summary evidence

New result:

- cleared for this validation target
- the new runner emits a structured JSON summary
- the automation worker summary and critic review both recognize the evidence
  oriented wrapper design

## Residual Review Concerns

The hardened contract cleared the prior four findings, but the regenerated
candidate still received `needs_revision` for new reasons:

1. dry-run currently returns `status = success`, which can blur the difference
   between runner success and artifact-production success
2. the runner status model only distinguishes `success` and `failed`, while the
   surrounding review contract expects room for a `partial` state
3. `preferred_base_script` is resolved relative to `Path.cwd()`, which is more
   brittle than resolving relative to repo root or the runner file
4. readonly behavior is still indirect because the wrapper delegates to another
   script without an explicit readonly enforcement layer
5. zero-PDF discovery behavior delegates forward instead of short-circuiting
   with a clearer reviewable outcome

These are new or refined concerns. They are not the same contract failures that
`BL-20260324-018` set out to fix.

## Conclusion

`BL-20260324-019` can be considered complete as a validation phase.

Why:

- the same-origin explicit regeneration path worked under governed conditions
- a fresh preview candidate was created from the current hardened contract
- the candidate was explicitly approved and executed once in real mode
- the phase truthfully proved that the prior four findings were cleared for this
  regenerated candidate
- the remaining `needs_revision` verdict comes from a new set of runner-contract
  concerns, which should be tracked as follow-up debt rather than leaving this
  validation phase ambiguous

## Follow-Up

This phase should open one new debt item for the residual runner-review gaps
instead of reusing `BL-20260324-019` indefinitely.

## Post-Run Gates

Commands run after evidence and backlog closeout:

```bash
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
bash scripts/premerge_check.sh
```

Observed result:

- backlog lint passed
- backlog sync passed with no remaining `phase=now` actionable items requiring
  mirroring
- `premerge_check.sh` passed with `Warnings: 0` and `Failures: 0`

## Gstack Checkpoint Note

No extra gstack checkpoint was run for this phase.

Reason:

- this phase was a live validation and evidence pass, not a new architecture or
  refactor phase
- the next follow-up debt may benefit from `review` before merge if it changes
  runner or contract code again
