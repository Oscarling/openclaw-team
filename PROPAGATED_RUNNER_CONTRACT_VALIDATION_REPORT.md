# Propagated Runner Contract Validation Report

## Objective

Validate whether the propagated source-side runner contract from
`BL-20260324-022` actually reaches a fresh same-origin preview candidate and
improves the generated runner behavior under one governed real execute.

This phase intentionally reuses the explicit same-origin regeneration path from
`BL-20260324-020` so the candidate can inherit the updated source-side contract
without relying on a fresh Trello card.

## Scope

In scope:

- one real Trello read-only smoke to confirm the target card is still reachable
- one fresh same-origin preview candidate created with a new
  `regeneration_token`
- one explicit approval decision for that candidate
- one real execute run in `test_mode=off`
- one grounded comparison between:
  - the post-propagation preview contract on the fresh candidate
  - the actual governed execute result from that candidate

Out of scope:

- changing `skills/execute_approved_previews.py`
- Git finalization
- Trello writeback / Done
- a second replay or another validation round in this phase

## Pre-Run Summary

Checked before the real run:

- reviewed `PROJECT_CHAT_AND_WORK_LOG.md`
- reviewed `BASELINE_FREEZE_NOTE.md`
- confirmed `origin` remote is present via `git remote -v`
- confirmed `/tmp/trello_env.sh` exists and still exports Trello credentials plus
  `TRELLO_BOARD_ID`
- confirmed OpenAI runtime values are still present in:
  - `secrets/openai_api_key.txt`
  - `secrets/openai_api_base.txt`
  - `secrets/openai_model_name.txt`
- confirmed this phase would stop at approval / execute and would not enter
  finalization or Trello Done

## Regenerated Candidate

Target origin:

- `trello:69c24cd3c1a2359ddd7a1bf8`

Regeneration token:

- `regen-20260324-bl023-001`

Real Trello read-only smoke:

```bash
source /tmp/trello_env.sh && python3 skills/trello_readonly_prep.py --smoke-read --board-id "$TRELLO_BOARD_ID" --limit 1
```

Observed result:

- read-only GET passed
- the reachable mapped card was still the intended target origin
- no Trello write operation occurred

Generated inbox payload:

- `inbox/trello-readonly-69c24cd3c1a2359ddd7a1bf8-regen-20260324-bl023-001.json`

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

- [preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.json)

Important pre-execute checks on the new preview:

- `approved = false`
- `source.regeneration_token = regen-20260324-bl023-001`
- dedupe key is
  `origin_regeneration:trello:69c24cd3c1a2359ddd7a1bf8:regen-20260324-bl023-001`
- the automation task now includes the propagated hints for:
  - `outcome_status_model`
  - `delegate_resolution`
  - `reviewed_delegate_contract`
- the automation contract profile is now
  `narrow_script_artifact_with_repo_reuse_and_reviewable_runner_contract`

## Approval And Execute

Approval file written:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.json)

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
  --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6 \
  --test-mode off
```

Observed result:

- `processed = 0`
- `rejected = 1`
- `skipped = 0`
- final decision:
  `critic_verdict=needs_revision`

Result sidecar:

- [approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.result.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6.result.json)

Final preview execution state:

- `approved = true`
- `execution.status = rejected`
- `execution.executed = true`
- `execution.attempts = 1`
- `finalization = null`

Worker outputs:

- Automation:
  [workspaces/automation/AUTO-20260324-856/output.json](/Users/lingguozhong/openclaw-team/workspaces/automation/AUTO-20260324-856/output.json)
- Critic:
  [workspaces/critic/CRITIC-20260324-277/output.json](/Users/lingguozhong/openclaw-team/workspaces/critic/CRITIC-20260324-277/output.json)
- Archived review artifact snapshot from this run:
  [pdf_to_excel_ocr_inbox_review.generated.md](/Users/lingguozhong/openclaw-team/runtime_archives/bl023/pdf_to_excel_ocr_inbox_review.generated.md)
- Archived generated script snapshot from this run:
  [pdf_to_excel_ocr_inbox_runner.generated.py](/Users/lingguozhong/openclaw-team/runtime_archives/bl023/pdf_to_excel_ocr_inbox_runner.generated.py)

## Runtime Archive Handling

This execute run overwrote the tracked baseline files:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `artifacts/reviews/pdf_to_excel_ocr_inbox_review.md`

To preserve the exact runtime evidence without leaving the branch in a
non-mergeable state:

- the generated runner and review were copied to `runtime_archives/bl023/`
- the tracked baseline files were restored from `HEAD` before merge-readiness
  gates were rerun

This keeps the real execute evidence available for audit while preserving the
baseline test contract on the tracked repository files.

## What The Propagated Contract Did Improve

The fresh candidate clearly inherited several of the source-side rules from
`BL-20260324-022`.

Evidence on the new preview candidate and generated runner:

- the propagated `automation_contract_profile` is present on the preview
- the propagated `contract_hints` are present on the preview
- the generated runner resolves delegation relative to the repo/script location
  rather than `Path.cwd()`
- the generated runner restricts delegation to
  `artifacts/scripts/pdf_to_excel_ocr.py`
- the generated runner reports `partial` for dry-run and zero-PDF cases

So this validation did prove that the source-side propagation phase reached the
fresh preview candidate and materially changed the generated artifact behavior.

## Residual Review Concerns

The propagated contract still did not produce a Critic-clean result.

The new review raised these remaining concerns:

1. the delegate `artifacts/scripts/pdf_to_excel_ocr.py` was not included in the
   review snapshot, so end-to-end conversion behavior still could not be audited
   from the review evidence alone
2. wrapper `success` is still grounded mainly in zero exit code plus non-empty
   `.xlsx` existence rather than stronger delegate-evidence standards
3. the embedded default description remains truncated (`cla...`), which weakens
   traceability fidelity in emitted summaries
4. `subprocess.run(..., capture_output=True)` still has no timeout, which the
   review treated as a robustness concern for smoke automation

These are not the same gaps as the original `BL-20260324-019` residual set.
They represent a new post-propagation review set and should be tracked
separately.

## Conclusion

`BL-20260324-023` can be considered complete as a validation phase.

Why:

- the same-origin explicit regeneration path still worked under governed
  conditions
- a fresh preview candidate was created under the propagated source-side
  contract
- the candidate did inherit the propagated runner-contract hints and profile
- one explicit approval and one real execute were completed
- the phase truthfully proved both:
  - what the propagation phase successfully changed
  - what residual Critic concerns still remain

## Follow-Up

This phase should open one new debt item for the residual delegate-evidence and
robustness review gaps instead of treating `BL-20260324-023` as an ambiguous
failure.
