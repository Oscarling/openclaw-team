# Full-chain Operational Validation Report

## Run Parameters
- Requested rounds: `5` (formal validation)
- Ingest mode: `python3 skills/ingest_tasks.py --once --test-mode off`
- Execute mode: `python3 skills/execute_approved_previews.py --once --preview-id <id> --test-mode off`
- Credential mode: command-level `OPENAI_API_KEY/OPENAI_API_BASE/OPENAI_MODEL_NAME` injection from local secret files (same as previous smoke fix)
- Gate policy:
  - `preview -> explicit approval -> execute` enforced
  - replay check executed without `--allow-replay`

## Overall Result
- Rounds completed: `5/5`
- Operationally passed rounds: `4/5`
- Failed rounds: `1/5` (Round 1 critic output contract failure)
- Mis-execution observed: `no`
- Duplicate execution observed: `no`
- Residual abnormal state:
  - `inbox` pending files: none
  - `processing` pending files: none
- Final conclusion: `unstable`

## Per-round Results
| Round | Inbox file path | Preview file path | Approval file path | Automation task_id | Critic task_id | Automation status | Critic status | Critic verdict | Final decision | Replay protection |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T013510Z-fullchain-r1.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-formal-r1-20260320t013510z-e4bb1dd202b4.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-formal-r1-20260320t013510z-e4bb1dd202b4.json` | `AUTO-20260320-563` | `CRITIC-20260320-173` | `success` | `failed` | `needs_revision` | `rejected` | `skipped (already_executed_use_allow_replay)` |
| 2 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T013555Z-fullchain-r2.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-formal-r2-20260320t013555z-d29013862815.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-formal-r2-20260320t013555z-d29013862815.json` | `AUTO-20260320-580` | `CRITIC-20260320-748` | `success` | `success` | `needs_revision` | `rejected` | `skipped (already_executed_use_allow_replay)` |
| 3 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T013755Z-fullchain-r3.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-formal-r3-20260320t013755z-1ce027fe9fda.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-formal-r3-20260320t013755z-1ce027fe9fda.json` | `AUTO-20260320-617` | `CRITIC-20260320-460` | `success` | `success` | `needs_revision` | `rejected` | `skipped (already_executed_use_allow_replay)` |
| 4 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T013845Z-fullchain-r4.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-formal-r4-20260320t013845z-50c5a43018f7.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-formal-r4-20260320t013845z-50c5a43018f7.json` | `AUTO-20260320-687` | `CRITIC-20260320-885` | `success` | `success` | `needs_revision` | `rejected` | `skipped (already_executed_use_allow_replay)` |
| 5 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T013936Z-fullchain-r5.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-formal-r5-20260320t013936z-5d3b11a962bd.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-formal-r5-20260320t013936z-5d3b11a962bd.json` | `AUTO-20260320-107` | `CRITIC-20260320-445` | `success` | `partial` | `needs_revision` | `rejected` | `skipped (already_executed_use_allow_replay)` |

## Required Validation Checks
- Every round started with empty inbox precheck: `pass`
- Every round produced preview first (`pending_approval`, `executed=false`): `pass`
- Every round required explicit approval before execute: `pass`
- Every round executed once after approval (`executed=true`, `attempts=1`): `pass`
- Replay protection without `allow-replay`: `pass` (`skipped` in all 5 rounds)
- Runtime logs present:
  - Round 1: automation and critic runtime logs present
  - Rounds 2-5: automation and critic runtime logs present

## Notable Issue
- Round 1 critic returned `status=failed` with error:
  - `success/partial output requires at least one artifact`
- This broke the “both artifacts generated” criterion for that round.

## Integrity / Safety
- Unapproved preview execution observed: `no`
- Duplicate execution observed: `no`
- Approval gate bypass observed: `no`

## Final Verdict
- `unstable`
- Reason: one of five rounds failed operational acceptance (Round 1 critic artifact contract failure), although control gate integrity and replay protection remained correct.
