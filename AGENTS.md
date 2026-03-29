# AGENTS.md

## Purpose

This file is the repo entrypoint for future contributors and agents. It summarizes
which documents are authoritative, which runtime rules are non-negotiable, and
which gates must be cleared before real integration work proceeds.

## Authority Order

Use one source of truth per question. Do not merge or freeze work by mixing old
snapshots with newer execution evidence.

1. Constitutional constraints:
   - `BASELINE_FREEZE_NOTE.md`
   - `RUNTIME_CONTRACT.md`
2. Open-work backlog:
   - `PROJECT_BACKLOG.md`
3. Current-state ledger:
   - `PROJECT_CHAT_AND_WORK_LOG.md`
4. Capability evidence for implemented behavior:
   - phase reports under repo root
   - `PROCESSED_FINALIZATION_REPORT.md`
5. Historical phase snapshot:
   - `MAINLINE_GAP_AUDIT.md` is a `Phase 8F` snapshot, not the live state ledger

## Non-Negotiable Runtime Rules

- Manager remains the single external entrypoint.
- External input defaults to `preview`, never direct execute.
- Approval must be explicit.
- Execute must remain a separate gate.
- Replay protection must remain intact.
- `needs_revision` is a business review result, not a control-chain failure.
- `git push` is a hard gate before Trello writeback / Done.

Do not refactor these files without a concrete blocker and a written reason:

- `dispatcher/worker_runtime.py`
- `skills/delegate_task.py`
- `skills/execute_approved_previews.py`

## Branch And Remote Policy

- A formal upstream remote must exist as `origin`.
- Human development must happen on topic branches such as `feat/*`, `fix/*`,
  or `phase8*/...`.
- `main` is reserved for reviewed code and must not receive direct pushes from
  humans or automation helpers.
- Automation-generated finalization output should go to a dedicated branch such as
  `automation/processed` or `ops/finalization/*`, then return to `main` through PR.
- Formal finalization runs must set explicit `GIT_PUSH_REMOTE` and `GIT_PUSH_BRANCH`.
  Missing values are a fail-closed condition.

## Required Gates

- Before any real Git / Trello finalization run:
  `docs/PRE_RUN_CHECKLIST.md`
- Before merge, freeze, or ship:
  `docs/PRE_MERGE_CHECKLIST.md`
- Repo-wide workflow and document responsibilities:
  `docs/ENGINEERING_WORKFLOW.md`

## Minimum Verification Commands

Run these commands as the minimum baseline when behavior changes touch the control
chain or processed finalization:

```bash
python3 scripts/backlog_lint.py
python3 -m unittest -v tests/test_backlog_lint.py
python3 -m unittest -v tests/test_argus_hardening.py
python3 -m unittest -v tests/test_processed_finalization.py
scripts/premerge_check.sh
scripts/preflight_finalization_check.sh <preview_json_path>
```

## Current Status Notes

- `PROJECT_BACKLOG.md` is the open-work source of truth. Review it before asking
  for merge, ship, or freeze decisions.
- `PROJECT_CHAT_AND_WORK_LOG.md` is the current-state ledger and should be tracked
  on the active branch before a formal phase closeout.
- Runtime-generated residue under `preview/`, `approvals/`, or `processed/` is not
  ordinary source diff. Classify it in `docs/RUNTIME_RESIDUE_REGISTRY.tsv` before
  merge or formal smoke; do not blindly reset it.
