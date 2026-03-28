# Provider Onboarding Snapshot Guard History Source Parity Report

## Objective

Strengthen summary/report consistency checks by enforcing history source parity
(`history_jsonl`) and strict summary-path validation settings in the same check
path.

## Scope

In scope:

- pass strict repo-path arguments into summary prevalidation inside consistency
  checker
- enforce normalized `history_jsonl` parity between summary and guard report
- extend tests for summary/report history source mismatch detection
- align dependent consistency tests that build synthetic summary payloads

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_consistency_check.py`
  - `tests/test_provider_onboarding_snapshot_guard_report_consistency_check.py`

## Validation Evidence

- checker now compares normalized summary/report `history_jsonl`
- checker now invokes summary validator with:
  - `repo_root`
  - `require_repo_paths`
- tests cover:
  - pass path with aligned history source
  - explicit history source mismatch fail path
  - report-consistency helper summary payload alignment

## Result

Summary/report consistency now validates both artifact schemas and source-path
parity, reducing the chance of cross-artifact drift hidden by metric-only
comparisons.

## Decision

BL-099 remains externally blocked; local snapshot-guard governance now includes
source-path parity as part of fail-closed consistency checks.
