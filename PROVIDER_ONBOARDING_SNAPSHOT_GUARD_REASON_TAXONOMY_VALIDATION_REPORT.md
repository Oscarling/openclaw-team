# Provider Onboarding Snapshot Guard Reason Taxonomy Validation Report

## Objective

Harden snapshot-guard report validation so reason keys and reason/count
partitions cannot drift semantically without merge-time failure.

## Scope

In scope:

- enforce allowed `reason_counts` taxonomy
- enforce `non_match_rows[].reason` domain (mismatch/unverified only)
- enforce reason-count partition checks across match/mismatch/unverified buckets
- add unit tests for taxonomy drift fail paths

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated script:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_validate.py`
- governance integration:
  - `scripts/premerge_check.sh`

## Validation Evidence

- validator now fails when:
  - unknown reason key appears in `reason_counts`
  - `non_match_rows` uses out-of-domain reason (for example `guard_match`)
  - reason-count partitions do not align with
    `guard_match_rows`/`guard_mismatch_rows`/`guard_unverified_rows`
- targeted unit tests cover both new fail paths and pass path.

## Result

Snapshot-guard report validation now covers semantic stability of reason
taxonomy, not just shape/count arithmetic.

## Decision

BL-099 remains externally blocked; local governance gained stronger
diagnostic-consistency guarantees for snapshot-guard evidence.
