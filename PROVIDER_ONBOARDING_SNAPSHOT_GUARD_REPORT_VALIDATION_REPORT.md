# Provider Onboarding Snapshot Guard Report Validation Report

## Objective

Add fail-closed schema/path validation for snapshot-guard detail report
artifacts so malformed payloads cannot pass merge gates silently.

## Scope

In scope:

- add dedicated snapshot-guard report validator script
- validate numeric/count invariants and row-level structure
- support optional repo-path enforcement for report row paths
- add unit tests and integrate into premerge checks
- update local runbook commands

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- new script:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- new tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_validate.py`
- premerge integration:
  - `scripts/premerge_check.sh`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- unit tests cover:
  - well-formed report pass path
  - invariant mismatch fail path
  - repo-path enforcement fail path
- runtime report validation passes with repo-path enforcement:
  - `runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json`
- premerge now validates generated report artifact:
  - `/tmp/provider_onboarding_snapshot_guard_report_premerge.json`

## Result

Snapshot-guard reporting now has structural integrity checks in addition to
generation checks, reducing risk of malformed metrics entering governance
evidence.

## Decision

BL-099 remains externally blocked; local hardening added fail-closed report
schema/path assurance and keeps onboarding evidence deterministic.
