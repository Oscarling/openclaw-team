# Processed Finalization Report

## Scope

This report covers the manager-side post-process closure added after `execution.status=processed`:

`processed -> git commit/push -> Trello Done`

The goal is to keep execution truth and post-process truth separate, preserve preview/approval/execute/replay-safe semantics, and make post-process failures auditable and retryable without rerunning Automation/Critic.

## Implemented

- Added [skills/finalize_processed_previews.py](/Users/lingguozhong/openclaw-team/skills/finalize_processed_previews.py) as a separate helper.
- The helper only processes previews that already satisfy:
  - `execution.status == "processed"`
  - `execution.executed == true`
- The helper persists post-process truth into:
  - `preview/<preview_id>.json -> finalization`
  - `approvals/<preview_id>.finalization.result.json`
- The helper enforces:
  - `git push` must succeed before Trello Done
  - completed finalization is replay-safe unless `--allow-replay-finalization` is explicitly set
  - failed post-process can be retried without rerunning execute

## Real Smoke

Real processed preview used:

- [preview/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.json)

Observed result:

- `execution.status = processed`
- finalization completed successfully
- git commit succeeded
- git push succeeded to a temporary bare remote
- Trello card moved to Done
- second run was replay-safe and skipped

Important evidence:

- [approvals/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.finalization.result.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.finalization.result.json)
- runtime-generated commit: `f07e35f4bcdf918c618ba7a7efc2009780d2418f`

## Failure Branch Coverage

Validated by [tests/test_processed_finalization.py](/Users/lingguozhong/openclaw-team/tests/test_processed_finalization.py):

- `critic fail` -> skipped, no finalization
- `worker partial` -> skipped, no finalization
- `runtime error` -> skipped, no finalization
- `missing git remote` -> failed with structured `finalization.git.push.reason = missing_git_push_remote`
- `git push failed` -> failed, commit hash preserved, retry resumes from push
- `missing Trello write credentials` -> failed with structured `finalization.trello.reason = missing_trello_write_credentials`
- `trello update failed` -> failed after successful push, retry resumes from Trello update
- replay after completed finalization -> skipped

Validation command:

```bash
python3 -m unittest -v tests/test_processed_finalization.py
```

Current result:

- `7 tests`
- `OK`

## State Truth and Retry Semantics

- `execution.*` remains the truth for Automation/Critic execution.
- `finalization.*` is the separate truth for git/trello post-process.
- Retry semantics are step-aware:
  - if commit already succeeded, retry does not re-commit
  - if push already succeeded, retry does not re-push
  - if Trello already succeeded, replay is blocked by default
- Environment blockers now land as structured failure state instead of only a generic exception string:
  - missing git remote
  - missing Trello write credentials

## Remaining Gaps

- The repository still has no configured upstream git remote:
  - `git remote -v` is empty
- Therefore, validated push semantics currently rely on an explicit temporary bare remote, not a production upstream remote.
- Trello Done resolution can work via list-name lookup, but production usage is more stable with explicit `TRELLO_DONE_LIST_ID`.

## Known Risks

- The repo currently has one dirty tracked preview file from the real smoke run:
  - [preview/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.json)
- This is audit evidence, not a logic failure, but it means runtime state can still leave tracked preview files dirty in the working tree.
- The helper fix committed in `bc93358` avoids adding preview files into future finalization commits, but it does not retroactively clean existing runtime residue.

## Next Step

The next minimal step is to provide a real upstream push target and run one formal finalization smoke against that target:

- configure `origin`, or
- pass `--git-remote` and `--git-branch`

After that, rerun one already-processed sample through:

`processed -> finalize_processed_previews -> git push -> Trello Done`

without changing execute or preview/approval semantics.
