# Full-chain Operational Validation Report V2

## Run Configuration
- Requested rounds: `5`
- Ingest command: `python3 skills/ingest_tasks.py --once --test-mode off`
- Execute command: `python3 skills/execute_approved_previews.py --once --preview-id <id> --test-mode off`
- Credential mode: command-level OPENAI env injection from `~/openclaw-team/secrets/*.txt`
- Control policy: `preview -> explicit approval -> execute`, with replay check (without `--allow-replay`)

## Per-round Summary
| Round | Inbox | Preview | Approval | Automation | Critic | Critic verdict | Review artifact | Final decision | Replay protection |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T021452Z-fullchain-v2-r1.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-v2-r1-20260320t021452z-61bcb7e21fee.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-v2-r1-20260320t021452z-61bcb7e21fee.json` | `AUTO-20260320-501 (success)` | `CRITIC-20260320-415 (success)` | `needs_revision` | `yes` | `rejected` | `pass` |
| 2 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T021554Z-fullchain-v2-r2.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-v2-r2-20260320t021554z-a8df2c084ad9.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-v2-r2-20260320t021554z-a8df2c084ad9.json` | `AUTO-20260320-947 (success)` | `CRITIC-20260320-664 (success)` | `needs_revision` | `yes` | `rejected` | `pass` |
| 3 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T021756Z-fullchain-v2-r3.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-v2-r3-20260320t021756z-ba3e0aee693e.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-v2-r3-20260320t021756z-ba3e0aee693e.json` | `AUTO-20260320-268 (success)` | `CRITIC-20260320-599 (success)` | `needs_revision` | `yes` | `rejected` | `pass` |
| 4 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T021858Z-fullchain-v2-r4.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-v2-r4-20260320t021858z-241fc650a2f6.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-v2-r4-20260320t021858z-241fc650a2f6.json` | `AUTO-20260320-493 (success)` | `CRITIC-20260320-752 (success)` | `pass` | `yes` | `processed` | `pass` |
| 5 | `/Users/lingguozhong/openclaw-team/inbox/task-20260320T022001Z-fullchain-v2-r5.json` | `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-v2-r5-20260320t022001z-0fe62dfe884b.json` | `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-v2-r5-20260320t022001z-0fe62dfe884b.json` | `AUTO-20260320-265 (success)` | `CRITIC-20260320-140 (success)` | `needs_revision` | `yes` | `rejected` | `pass` |

## A. Chain Stability
- Rounds completed: `5/5`
- Chain stability conclusion: `stable`
- Critic failed count: `0`
- Critic missing review artifact count: `0`
- Replay protection passed: `5/5`
- Mis-execution detected: `no`
- Duplicate execution detected: `no`
- Residual inbox pending: `0`
- Residual processing pending: `0`

## B. Business Review Outcome
- Critic verdict pass: `1`
- Critic verdict needs_revision: `4`
- Critic verdict fail: `0`
- Critic status partial: `0`
- Final decision processed: `1`
- Final decision rejected: `4`
- needs_revision reason breakdown: `{"artifact_capability_gap_or_placeholder_behavior": 3, "other_explainable_review_reason": 1}`
- needs_revision reasons consistent/explainable: `yes`

## Separation Rule Applied
- `needs_revision` is treated as business review outcome, not chain-failure by itself.
- Chain stability only fails on control-chain faults (gate/replay/misexecution), Critic `failed`, or missing review artifact.
