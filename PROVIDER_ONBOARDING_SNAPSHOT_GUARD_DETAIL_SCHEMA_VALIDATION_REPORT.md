# Provider Onboarding Snapshot Guard Detail Schema Validation Report

## Objective

Enforce reason-specific schema for `non_match_rows[].detail` so row-level
snapshot-guard diagnostics stay machine-parseable and semantically consistent.

## Scope

In scope:

- validate reason-specific detail fields and types
- validate HTTP mismatch detail maps as non-empty status-code counters
- keep existing taxonomy/count/order checks
- add unit coverage for detail-shape drift failures

Out of scope:

- provider/key remediation
- canary replay execution

## Deliverables

- updated validator:
  - `scripts/provider_onboarding_snapshot_guard_report_validate.py`
- updated tests:
  - `tests/test_provider_onboarding_snapshot_guard_report_validate.py`
- inherited merge gate:
  - `scripts/premerge_check.sh`

## Validation Evidence

- validator now fails when:
  - `guard_mismatch_block_reason` detail is missing
    `entry_block_reason`/`snapshot_block_reason`
  - unverified reasons omit `detail.assessment_snapshot_json`
  - HTTP mismatch detail payloads are malformed
- unit tests cover new detail schema fail paths.

## Result

Snapshot-guard row-level mismatch artifacts now carry reason-aligned detail
contracts, reducing ambiguity in downstream diagnostics.

## Decision

BL-099 remains externally blocked; local governance gained stricter detail-level
semantic validation.
