# Provider Onboarding Snapshot Guard Summary Path Validation Report

## Objective

Harden snapshot-guard summary validation by requiring `history_jsonl` to exist as
an explicit summary field and enforcing repo-root path scope in strict mode.

## Scope

In scope:

- require `history_jsonl` in snapshot-guard summary validator
- add strict repo-root scoped path check via `--repo-root --require-repo-paths`
- extend unit tests for missing-history and repo-scope pass/fail paths
- standardize strict invocation in premerge and runbook

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated validator:
  - `scripts/provider_onboarding_snapshot_guard_summary_validate.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_summary_validate.py`
- strict gate integration:
  - `scripts/premerge_check.sh`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- validator now rejects missing/empty `history_jsonl`
- strict mode now verifies `history_jsonl` resolves under `--repo-root`
- tests cover:
  - missing `history_jsonl` rejection
  - strict repo-scope pass/fail paths
  - strict main-path invocation success

## Result

Snapshot-guard summary artifacts now carry explicit history source metadata with
fail-closed repo-scope validation in merge and operator paths.

## Decision

BL-099 remains externally blocked; local governance strengthened summary source
path integrity so downstream checks consume trusted path metadata.
