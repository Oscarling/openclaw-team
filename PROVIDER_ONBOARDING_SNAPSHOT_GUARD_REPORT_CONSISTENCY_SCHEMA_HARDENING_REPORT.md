# Provider Onboarding Snapshot Guard Report Consistency Schema Hardening Report

## Objective

Harden persisted snapshot-guard report consistency checks by validating schema,
path integrity, and source-history path parity before field-level comparison.

## Scope

In scope:

- add schema/path validation step to report-consistency checker
- add `--require-repo-paths` support for stricter enforcement
- compare normalized `history_jsonl` path between expected and actual report
- extend unit tests for new fail paths

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated checker:
  - `scripts/provider_onboarding_snapshot_guard_report_consistency_check.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_consistency_check.py`
- premerge update:
  - `scripts/premerge_check.sh`

## Validation Evidence

- checker now fail-closes on malformed report schema before diff compare.
- checker now fail-closes when normalized `history_jsonl` source path diverges.
- unit tests cover:
  - history-path mismatch detection
  - stale report mismatch
  - schema-invalid report fail path
  - matching report pass path

## Result

Persisted report freshness checks now include stricter input integrity and
source-parity guarantees, reducing false confidence from malformed artifacts.

## Decision

BL-099 remains externally blocked; local governance strengthened persisted
snapshot-guard report freshness validation semantics.
