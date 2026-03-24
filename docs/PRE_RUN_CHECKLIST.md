# Pre-Run Checklist

Use this checklist before any real integration run that can touch Git, Trello, or
formal upstream state.

## Scope

This checklist is mandatory before:

- `processed -> git push -> Trello Done`
- real Trello read smoke
- real Trello writeback
- any formal upstream smoke

## Required Checks

- [ ] I reviewed the current-state ledger:
      `PROJECT_CHAT_AND_WORK_LOG.md`
- [ ] I reviewed the constitutional constraints:
      `BASELINE_FREEZE_NOTE.md`
- [ ] `git status --short` has no unclassified residue
- [ ] If `preview/`, `approvals/`, or `processed/` files are dirty, I have already
      classified them under the runtime audit residue policy and recorded them in
      `docs/RUNTIME_RESIDUE_REGISTRY.tsv`
- [ ] I know the exact command I will run
- [ ] I know what evidence file will be updated after the run
- [ ] I know what rollback or retry path I will use if push or Trello update fails

## Additional Checks For Git Push / Finalization Runs

- [ ] The target sample already satisfies:
      `execution.status == processed`
- [ ] `git remote -v` is non-empty
- [ ] `GIT_PUSH_REMOTE` is set explicitly
- [ ] `GIT_PUSH_BRANCH` is set explicitly
- [ ] The target push branch matches the branch policy and is not an accidental
      fallback to `main`

## Additional Checks For Trello API Runs

- [ ] `TRELLO_API_KEY` is set
- [ ] `TRELLO_API_TOKEN` is set

## Additional Checks For Trello Done / Writeback Runs

- [ ] `TRELLO_DONE_LIST_ID` is set, or I have documented why list-name resolution
      is acceptable for this run

## Minimum Commands

```bash
git remote -v
git status --short
```

For finalization work, also run:

```bash
python3 -m unittest -v tests/test_processed_finalization.py
scripts/preflight_finalization_check.sh <preview_json_path>
```

## Fail-Closed Rule

If remote, branch, credential, or sample state is ambiguous, stop. Do not run a
formal integration command on assumption.
