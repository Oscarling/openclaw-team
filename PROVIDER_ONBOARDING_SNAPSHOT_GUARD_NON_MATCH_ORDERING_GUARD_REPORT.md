# Provider Onboarding Snapshot Guard Non Match Ordering Guard Report

## Objective

Enforce deterministic ordering and uniqueness of `non_match_rows` in
snapshot-guard report validation.

## Scope

In scope:

- reject non-increasing `history_line` ordering in `non_match_rows`
- reject duplicate `history_line` values
- add unit coverage for ordering/duplication failure
- keep existing premerge report-validation gate path

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated validator:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_validate.py`
- inherited gate:
  - `scripts/premerge_check.sh`

## Validation Evidence

- validator now enforces:
  - `non_match_rows history_line values must be strictly increasing and unique`
- targeted unit test covers duplicate/non-increasing failure path.

## Result

Row-level mismatch evidence now has deterministic ordering guarantees, reducing
triage ambiguity and duplicate-line drift.

## Decision

BL-099 remains externally blocked; local evidence quality improved with stricter
row-order/uniqueness validation.
