# Pre-Merge And Pre-Ship Checklist

Use this checklist before merging, freezing a phase, or calling a real integration
step complete.

## Required Checks

- [ ] The change is on the correct branch and not being developed directly on `main`
- [ ] The PR description includes scope, non-goals, risks, and rollback notes
- [ ] Repo-level baseline tests passed
- [ ] Phase-specific smoke and regression runs passed
- [ ] If this change touched finalization behavior, I ran:
      `python3 -m unittest -v tests/test_processed_finalization.py`
- [ ] If this change touched Trello read-only ingress behavior, I ran:
      `python3 -m unittest -v tests/test_trello_readonly_ingress.py`
- [ ] If this change touched the control chain, I ran:
      `python3 -m unittest -v tests/test_argus_hardening.py`
- [ ] If this change touched real Git / Trello integration, the pre-run checklist
      was completed
- [ ] `PROJECT_BACKLOG.md` was reviewed as part of this merge / ship decision
- [ ] Relevant backlog items have updated `status`, `phase`, and `last_reviewed_at`
- [ ] Any newly discovered sideline / blocker / debt / future item was recorded
      before requesting review
- [ ] GitHub issue mirroring was updated, or an explicit defer reason was recorded
- [ ] `PROJECT_CHAT_AND_WORK_LOG.md` is updated or explicitly confirmed unchanged
- [ ] The relevant evidence report is updated or explicitly confirmed unchanged
- [ ] Any stale snapshot document is labeled as historical if newer evidence now
      supersedes it
- [ ] Worktree residue has been classified under the runtime audit residue policy
- [ ] Any kept runtime residue is registered in `docs/RUNTIME_RESIDUE_REGISTRY.tsv`
- [ ] Runtime-generated audit files are either intentionally retained with evidence,
      or moved out of the merge path
- [ ] The phase exit condition is explicitly satisfied
- [ ] At least one structured review happened before merge

## Minimum Evidence To Attach To A PR Or Freeze Decision

- test commands run
- smoke / regression result summary
- affected docs
- remaining risks
- rollback or retry path

## Minimum Commands

```bash
python3 scripts/backlog_lint.py
scripts/premerge_check.sh
```

## Ship Rule

No phase is "done" if the code changed but the ledger, evidence, or gate status was
left stale.
