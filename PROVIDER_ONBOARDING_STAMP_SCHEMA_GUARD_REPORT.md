# Provider Onboarding Stamp Schema Guard Report

## Context

`BL-20260326-099` remains externally blocked. While continuing local hardening,
operator retest habits introduced non-date suffixes in `--stamp` (for example
`20260329_retest`), which violated history schema (`stamp` must be `YYYYMMDD`)
and forced manual repair.

## Objective

Add a fail-closed guard in `provider_onboarding_gate.py` so invalid stamps are
rejected before probe execution and before history writes.

## Implementation

- `scripts/provider_onboarding_gate.py`
  - adds `validate_stamp(...)`:
    - requires regex `^\d{8}$`
    - requires calendar-valid date via `datetime.strptime(..., "%Y%m%d")`
  - `main()` now validates `args.stamp` early and exits `2` on invalid input
    without calling probe/assess commands
- `tests/test_provider_onboarding_gate.py`
  - adds `test_main_rejects_invalid_stamp_format`
  - adds `test_main_rejects_invalid_stamp_date`
  - both assert fail-fast return code `2` and zero downstream command calls
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - documents strict `--stamp` rule and guidance:
    - use valid `YYYYMMDD`
    - do not add `_retest` suffixes
    - use per-run `timestamp` + immutable snapshots for same-day differentiation

## Verification Snapshot (2026-03-29)

- `python3 -m unittest -v tests/test_provider_onboarding_gate.py` (passed)
- `python3 -m unittest -v tests/test_provider_handshake_assess.py tests/test_project_delivery_status.py` (passed)
- `python3 scripts/backlog_lint.py` (passed)

## Outcome

Provider onboarding history integrity is now protected at source:
invalid stamp inputs are blocked before runtime artifacts and history JSONL can
drift from schema constraints.
