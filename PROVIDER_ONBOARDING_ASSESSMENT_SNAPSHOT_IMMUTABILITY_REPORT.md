# Provider Onboarding Assessment Snapshot Immutability Report

## Objective

Prevent history pointer drift caused by reusable assessment file paths being
overwritten across repeated same-day runs.

## Scope

In scope:

- add immutable assessment snapshot capture in one-shot gate history writes
- store snapshot path in history rows (`assessment_snapshot_json`)
- make validator enforce snapshot path scope when repo-path checks are enabled
- update backfill and gap-report tools to prefer snapshot path when available

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- gate snapshot persistence:
  - `scripts/provider_onboarding_gate.py`
- validator update:
  - `scripts/provider_onboarding_history_validate.py`
- backfill/gap tooling updates:
  - `scripts/provider_onboarding_history_backfill.py`
  - `scripts/provider_onboarding_history_backfill_gaps.py`
- tests:
  - `tests/test_provider_onboarding_gate.py`
  - `tests/test_provider_onboarding_history_validate.py`
  - `tests/test_provider_onboarding_history_backfill.py`
  - `tests/test_provider_onboarding_history_backfill_gaps.py`

## Validation Evidence

- gate tests now verify snapshot file creation under configured temp snapshot
  directory during history append flows
- validator rejects non-repo snapshot paths under `--require-repo-paths`
- backfill and gap-report logic use snapshot path first when present

## Result

Future history rows can bind to immutable per-run assessment snapshots, reducing
the risk of historical pointer drift and improving safe backfill accuracy.

## Decision

BL-099 remains externally blocked; local evidence governance now includes
forward-looking immutability controls for assessment references.
