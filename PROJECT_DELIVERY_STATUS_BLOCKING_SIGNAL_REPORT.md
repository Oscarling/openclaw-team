# Project Delivery Status Blocking Signal Report

## Context

`BL-20260326-099` is externally blocked. The status board already exposed
`delivery_state` and onboarding summary fields, but premerge/operator workflows
still required manual interpretation to identify whether blocking was at
handshake stage or post-handshake promotion stage.

## Objective

Add a deterministic `blocking_signal` contract to delivery-status output and
surface it in premerge checks for faster triage without changing gating policy.

## Implementation

- `scripts/project_delivery_status.py`
  - `_build_delivery_state(...)` now also returns `blocking_signal`:
    - `stage`:
      - `handshake_gate`
      - `controlled_replay_promotion`
      - `provider_chain`
      - `unknown`
    - `reason`:
      - concrete blocker reason (for example
        `provider_account_arrearage`, `auth_or_access_policy_block`,
        `provider_billing_arrearage`)
  - payload now includes top-level `blocking_signal` object
  - markdown output now includes:
    - `blocking_stage`
    - `blocking_reason`
- `tests/test_project_delivery_status.py`
  - verifies `blocking_signal` for:
    - blocked handshake case
    - ready chain-clear case (empty signal)
    - handshake-ready but BL-099 blocked case (`controlled_replay_promotion`)
    - summary-missing unknown case
- `scripts/premerge_check.sh`
  - after status-board smoke check, calls
    `scripts/project_delivery_signal.py` on
    `/tmp/project_delivery_status_premerge.json` and emits one concise signal
    line:
    - `[PASS]` when `ready_for_replay`
    - `[WARN]` with `state/stage/reason` otherwise
  - does not alter fail-closed semantics; this is visibility hardening.
- `scripts/project_delivery_signal.py`
  - provides a tested extraction contract from status JSON to compact
    `tsv/json` signal payload (`delivery_state`, `blocking_stage`,
    `blocking_reason`, onboarding latest block/timestamp fields)
- `tests/test_project_delivery_signal.py`
  - covers extraction with/without optional fields, TSV rendering, and
    fail-fast require-delivery-state behavior
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - documents `blocking_signal` meaning and stage/reason interpretation.

## Verification Snapshot (2026-03-29)

- `python3 -m unittest -v tests/test_project_delivery_status.py` (passed)
- `python3 -m unittest -v tests/test_project_delivery_signal.py` (passed)
- `bash -n scripts/premerge_check.sh` (passed)
- `python3 scripts/project_delivery_status.py --backlog PROJECT_BACKLOG.md --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json --repo-root /Users/lingguozhong/openclaw-team --output-json /tmp/project_delivery_status_signal.json --output-md /tmp/project_delivery_status_signal.md` (passed; output includes `blocking_signal` and markdown includes `blocking_stage`/`blocking_reason`)

## Outcome

Blocked-provider phase triage is now direct and deterministic in both status
artifacts and premerge output, reducing manual interpretation while preserving
existing gates.
