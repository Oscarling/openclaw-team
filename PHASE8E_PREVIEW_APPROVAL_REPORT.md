# Phase 8E Preview + Approval Control Report

## Scope
This phase adds a control layer so external input cannot execute immediately.

Guardrails preserved:
- Manager remains the only dispatch entry.
- Adapter remains normalization/validation only.
- No Trello write operations.
- No Git automation behavior.
- No edits to `skills/delegate_task.py` or `dispatcher/worker_runtime.py`.

## Files Added / Updated
- Added: `skills/execute_approved_previews.py`
- Added: `preview/.gitkeep`
- Added: `approvals/.gitkeep`
- Added: `PHASE8E_PREVIEW_APPROVAL_REPORT.md`
- Updated: `skills/ingest_tasks.py`
- Updated: `.gitignore`
- Updated: `docs/external_task_format.md`

## Preview Structure
`skills/ingest_tasks.py` now converts each valid inbox input into `preview/<preview_id>.json` with:
- `preview_id`
- `created_at`
- `approved` (default `false`)
- `source` (`kind`, `origin_id`, `received_at`, `inbox_file`)
- `external_input` (normalized title/description/labels/metadata/request_type/input)
- `task_summary` (automation + critic summary)
- `internal_tasks` (full automation + critic task payloads, for Manager-only execution path)
- `expected_artifacts`
- `dedupe_keys`
- `risk_warnings`
- `execution` (default `pending_approval`, `executed=false`, `attempts=0`)

## Approval Mechanism
- Explicit approval file required: `approvals/<preview_id>.json`
- Minimum decision field: `approved` (`true` allows execution)
- Execution entrypoint: `skills/execute_approved_previews.py`
- Enforcement:
  - Approval missing => no execution
  - `approved=false` => skipped, no execution
  - Already executed preview => skipped unless `--allow-replay` is explicitly provided
- Execution writes:
  - preview execution update (`execution.status`, `executed_at`, `attempts`)
  - approval sidecar: `approvals/<preview_id>.result.json`

## Validation Scenarios (Phase 8E)
Run timestamp: `20260319T134324Z`

1) Valid input + approved => executed successfully
- Inbox file: `phase8e_case_a_valid_20260319T134324Z.json`
- Preview created: `preview-phase8e-a-20260319t134324z-a2f488a0b2bf`
- Approval: `approved=true`
- Execution result:
  - status: `processed`
  - reason: `critic_verdict=pass`
  - preview execution: `executed=true`, `attempts=1`

2) Valid input + unapproved => preview only, not executed
- Inbox file: `phase8e_case_b_valid_unapproved_20260319T134324Z.json`
- Preview created: `preview-phase8e-b-20260319t134324z-3e6e6978fe31`
- Approval: `approved=false`
- Execution result:
  - skipped (`approval_flag_not_true`)
  - preview execution remains `pending_approval`, `executed=false`, `attempts=0`

3) Invalid input => rejected, never enters execution
- Inbox file: `phase8e_case_c_invalid_20260319T134324Z.json`
- Ingest result: `rejected`
- Reason: `title is required and must be a non-empty string`
- No preview dispatch occurred

## Control Chain Conclusion
`unapproved cannot execute` is enforced:
- Ingest only creates preview, never dispatches workers.
- Only approved previews are eligible for Manager-side execution.
- Unapproved previews remain in pending state.

## Remaining Non-goals
- Trello writeback remains disabled.
- Real Git push automation remains disabled.
