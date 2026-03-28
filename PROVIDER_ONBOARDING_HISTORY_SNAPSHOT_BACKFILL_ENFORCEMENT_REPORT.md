# Provider Onboarding History Snapshot Backfill Enforcement Report

## Objective

Eliminate legacy assess-row snapshot gaps and enforce fail-closed snapshot/file
integrity in onboarding history validation.

## Scope

In scope:

- add a dedicated backfill tool for missing `assessment_snapshot_json`
- backfill legacy assess rows to immutable snapshot files
- strengthen validator with assess-row snapshot required check
- strengthen validator with referenced-file existence check
- integrate stricter checks into premerge and runbook

Out of scope:

- external provider/key remediation
- canary replay execution

## Deliverables

- snapshot backfill tool:
  - `scripts/provider_onboarding_history_snapshot_backfill.py`
- validator hardening:
  - `scripts/provider_onboarding_history_validate.py`
- premerge gate updates:
  - `scripts/premerge_check.sh`
- tests:
  - `tests/test_provider_onboarding_history_snapshot_backfill.py`
  - `tests/test_provider_onboarding_history_validate.py`
- docs:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- snapshot backfill tool writes immutable snapshot pointers for legacy assess
  rows and preserves backup safety controls
- validator now supports strict flags:
  - `--require-snapshot-for-assess`
  - `--require-existing-files`
- premerge now enforces strict history validation and snapshot-backfill
  dry-run check
- runtime history artifact updated with snapshot pointers for existing rows

## Result

Onboarding history now has stronger immutability guarantees for both new and
legacy assess rows, and merge-time validation fails closed when snapshot/file
integrity drifts.

## Decision

BL-099 remains externally blocked; local governance is further hardened to keep
history evidence deterministic and audit-safe while waiting for usable
provider/base+key.
