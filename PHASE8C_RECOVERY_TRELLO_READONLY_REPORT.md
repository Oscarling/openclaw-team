# Phase 8C Recovery Verification + Trello Read-only Prep

## Scope
This phase verifies two goals without touching Phase 6 core runtime:
1. Recovery reliability of local inbox flow (`inbox -> processing -> processed/rejected`)
2. Trello read-only preparation (mapping + read-only smoke pathway), with no Trello write actions

Constraints honored:
- Manager remains the only dispatch entry
- Adapter remains a normalization component (no worker dispatch inside adapter)
- No changes to `skills/delegate_task.py` or `dispatcher/worker_runtime.py`
- No real Git automation integration
- No Trello writeback / status update / comment / create / delete

## Files Added / Updated
- Added:
  - `adapters/trello_readonly_adapter.py`
  - `adapters/samples/trello_card_fixture.json`
  - `skills/trello_readonly_prep.py`
  - `PHASE8C_RECOVERY_TRELLO_READONLY_REPORT.md`
- Updated:
  - `skills/trello_readonly_prep.py` (import path fix during execution)

## Recovery Scenario Verification
Recovery was verified with controlled processing leftovers and end-to-end ingest runs.

### Scenario A: processing leftover resumed and completed
- Injected a valid file directly into `processing/`:
  - `phase8c_recovery_a_<run_tag>.json`
- Ran ingest once.
- Result:
  - `processing_recovered=1`
  - `processed=1`, `rejected=0`
  - output moved to `processed/`
  - `.result.json` persisted
  - no duplicate execution evidence

### Scenario B: processing leftover duplicate correctly skipped
- Injected another file directly into `processing/` using same `origin_id` as scenario A.
- Ran ingest once.
- Result:
  - `processing_recovered=1`
  - `processed=0`, `rejected=1`, `duplicate_skipped=1`
  - output moved to `rejected/`
  - `.result.json` includes duplicate key reason
  - no worker dispatch execution performed for duplicate item

## Multi-file Recovery Regression
Executed one mixed run with 8 files:
- valid: 4 (including recovered processing files)
- invalid: 2
- duplicate: 2
- includes both inbox and processing injected inputs

Observed run metrics:
- `processed=4`
- `rejected=4`
- `duplicate_skipped=2`
- `inbox_claimed=5`
- `processing_recovered=3`

Validation checks:
- no task cross-read/overwrite detected
- duplicate and invalid inputs were rejected with explicit reasons
- processed inputs generated task + runtime evidence
- processing directory returned to clean state (`.gitkeep` only)
- no abnormal residual containers observed

Raw evidence artifact:
- `/tmp/phase8c/phase8c_runner_result_20260319T100657Z.json`

## Trello Read-only Preparation
Implemented read-only preparation layer:
- Adapter: `adapters/trello_readonly_adapter.py`
  - maps Trello card payload -> normalized external input format
  - injects `source.provider=trello`, `source.mode=readonly`
  - does not dispatch workers
- Manager-side helper: `skills/trello_readonly_prep.py`
  - fixture-based mapping output
  - optional `--smoke-read` uses GET-only Trello API path
  - defines required env and minimal scope

Required env/scope documented by helper:
- Credentials:
  - `TRELLO_API_KEY`
  - `TRELLO_API_TOKEN`
- Read scope (at least one):
  - `TRELLO_BOARD_ID` or `TRELLO_LIST_ID`

Trello write operations explicitly not implemented:
- no card writes
- no status/list movement
- no comments
- no create/delete

## Read-only Smoke Check
- Fixture mapping: **Pass**
- Real Trello read-only smoke check: **Blocked**
  - reason: missing `TRELLO_API_KEY` and `TRELLO_API_TOKEN`
  - no fake success used

## Still Not Done (Explicit)
- Real Git automation integration: not implemented
- Trello writeback flow: not implemented
