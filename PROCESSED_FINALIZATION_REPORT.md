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

## Formal Upstream Smoke

On `2026-03-24`, the repo completed a fresh formal smoke against the real
configured GitHub remote:

- remote: `origin`
- branch: `ops/finalization/formal-smoke-20260324`
- Trello card: `69c1fff1b3339965c25783b7`
- preview used:
  - [preview/preview-trello-69c1fff1b3339965c25783b7-cb69af50b8ba.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c1fff1b3339965c25783b7-cb69af50b8ba.json)

Formal result:

- `execution.status = processed`
- finalization completed successfully
- git push succeeded to `origin/ops/finalization/formal-smoke-20260324`
- Trello card moved to Done list `69be462743bfa0038ca10f91`
- finalization commit: `001ac972b13bdd21e4fd39e585bb66a30210863b`

Required hardening discovered and implemented during this formal smoke:

- `bd4d75e` Harden formal preview smoke execution
  - fix Critic verdict extraction so embedded contract text cannot override the
    real review verdict line
  - allow `test_mode` execution without requiring Docker client initialization
  - allow preflight to admit only the supplied preview's governed candidate
    paths instead of blanket failing on all non-runtime dirty files

Formal smoke evidence:

- [approvals/preview-trello-69c1fff1b3339965c25783b7-cb69af50b8ba.finalization.result.json](/Users/lingguozhong/openclaw-team/approvals/preview-trello-69c1fff1b3339965c25783b7-cb69af50b8ba.finalization.result.json)
- finalization commit: `001ac972b13bdd21e4fd39e585bb66a30210863b`
- hardening commit: `bd4d75e`

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

- `TRELLO_DONE_LIST_ID` is still optional in the active setup and current smoke
  relied on board list-name resolution.
- The formal-smoke hardening commit should still return through the ordinary
  reviewed code path before merge to `main`.

## Known Risks

- The old failed replay mutation of the historical sample is now archived, not
  left as working-tree residue:
  - [preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.failed-replay-2026-03-24.json](/Users/lingguozhong/openclaw-team/docs/archive/runtime_residue/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.failed-replay-2026-03-24.json)
  - [preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.failed-replay-2026-03-24.md](/Users/lingguozhong/openclaw-team/docs/archive/runtime_residue/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.failed-replay-2026-03-24.md)
- The helper fix committed in `bc93358` avoids adding preview files into future
  finalization commits, but archive discipline is still required if a human
  replays old finalized samples locally.

## Next Step

The next minimal standard-process step is to move the formal-smoke hardening
back through an ordinary reviewed code branch / PR and optionally pin
`TRELLO_DONE_LIST_ID` in the execution environment so future formal runs do not
depend on list-name lookup.
