# Full-chain Operational Validation Report

## Run Parameters
- `ROUNDS=1` (smoke validation)
- Mode policy:
  - ingest: `--test-mode off`
  - execute approved previews: `--test-mode off`
- Gate policy:
  - no bypass of preview/approval
  - no `allow-replay` in replay-protection check

## Overall Summary
- Total rounds attempted: `1`
- Round success: `0`
- Round failed/blocked: `1`
- Final conclusion: `blocked`

Primary blocker observed in Round 1:
- Automation execution failed due missing LLM API key in runtime worker environment:
  - `Missing API key. Checked: openai_api_key, api_key, OPENAI_API_KEY, API_KEY`

## Per-round Record

### Round 1
- Inbox file:
  - `/Users/lingguozhong/openclaw-team/processed/task-20260320T012023Z-fullchain-round1.json`
- Preview file:
  - `/Users/lingguozhong/openclaw-team/preview/preview-fullchain-r1-20260320t012023z-ffa88c148dac.json`
- Approval file:
  - `/Users/lingguozhong/openclaw-team/approvals/preview-fullchain-r1-20260320t012023z-ffa88c148dac.json`
- Automation task_id:
  - `AUTO-20260320-710`
- Critic task_id:
  - `CRITIC-20260320-809`

Execution path evidence:
1. `inbox -> ingest` succeeded
  - preview generated
  - preview state before approval:
    - `execution.status = pending_approval`
    - `execution.executed = false`
2. explicit approval created
3. `execute_approved_previews` run with `--test-mode off`
  - result: `rejected`
  - reason: Automation task failed (missing API key)
4. preview state after execution attempt:
  - `execution.status = rejected`
  - `execution.executed = true`
  - `execution.attempts = 1`

Artifact / runtime evidence:
- Automation result: `failed`
- Critic result: not present (not executed after Automation failure)
- Artifacts generated: none
- Task evidence:
  - automation task json exists:
    - `/Users/lingguozhong/openclaw-team/tasks/AUTO-20260320-710.json`
  - critic task json not present:
    - `/Users/lingguozhong/openclaw-team/tasks/CRITIC-20260320-809.json`
- runtime.log evidence:
  - `/Users/lingguozhong/openclaw-team/workspaces/automation/runtime.log` not found
  - `/Users/lingguozhong/openclaw-team/workspaces/critic/runtime.log` not found

Replay protection check:
- Re-ran execute command for same preview without `allow-replay`
- Result: `skipped`
- Decision reason: `already_executed_use_allow_replay`
- Replay protection status: `effective`

## Control-chain Integrity Checks
- Mis-execution (unapproved preview executed): `not observed`
- Duplicate execution (same preview auto-rerun): `not observed`
- Approval gate bypass: `not observed`
- Residual abnormal state:
  - `inbox/` pending files: none
  - `processing/` pending files: none

## Final Verdict
- Status: `blocked`
- Reason: real execution environment lacks required LLM API key for worker runtime.
- Next action before raising to `ROUNDS=5`:
  - inject valid API key/base/model environment into actual worker execution environment and re-run smoke round.
