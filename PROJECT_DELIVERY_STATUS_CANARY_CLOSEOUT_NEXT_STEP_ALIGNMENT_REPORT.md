# Project Delivery Status Canary Closeout Next-Step Alignment Report

## Context

After `BL-20260329-160` closed with a passing 4-sample DeepSeek canary window,
`project_delivery_status.py` still emitted a generic next-step prompt:
"进入 controlled replay 与 canary 收尾流程。"

That guidance was stale once canary closeout was already done.

## Change

- Updated `scripts/project_delivery_status.py`:
  - added `REPLAY_CANARY_CLOSEOUT_ID = BL-20260329-160`
  - when provider chain is clear and onboarding is `ready`, status remains
    `ready_for_replay` for compatibility
  - if `BL-20260329-160` is `done`, `next_steps` now points directly to
    finalization preflight prerequisites (`GIT_PUSH_REMOTE`,
    `GIT_PUSH_BRANCH`, `TRELLO_*`, clean working tree)
- Added regression test:
  - `test_build_status_payload_points_to_preflight_after_canary_closeout`
  - file: `tests/test_project_delivery_status.py`

## Result

- Delivery status output now keeps enum compatibility while presenting the
  correct operational next step after canary closeout.
- No contract drift in existing status gating (`delivery_state` unchanged).

## Verification

- `python3 -m unittest -v tests/test_project_delivery_status.py` (passed)
- `python3 scripts/project_delivery_status.py --backlog PROJECT_BACKLOG.md --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json --repo-root /Users/lingguozhong/openclaw-team --output-json runtime_archives/bl100/tmp/project_delivery_status_after_bl160_done.json --output-md runtime_archives/bl100/tmp/project_delivery_status_after_bl160_done.md` (passed)
- `bash scripts/premerge_check.sh` (passed, `Failures: 0`)
