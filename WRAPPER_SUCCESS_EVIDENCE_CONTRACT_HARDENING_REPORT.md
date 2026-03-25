# Wrapper Success Evidence Contract Hardening Report

## Objective

Complete `BL-20260325-040` by hardening source-side contract guidance so
generated wrapper scripts cannot overclaim success without explicit delegate
output-write attestation consistency.

## Scope

In scope:

- strengthen local inbox automation contract hints for success evidence
- strengthen automation task constraints and acceptance criteria for field-level
  success attestation
- focused adapter regression coverage

Out of scope:

- fresh governed live Trello validation run
- runtime worker implementation changes
- git finalization / Trello Done writeback

## Changes

### 1) Strengthened automation contract hints to field-level requirements

Updated `adapters/local_inbox_adapter.py`:

- expanded `contract_hints.delegate_success_evidence` from high-level wording to
  explicit gating conditions for wrapper success:
  - `status=success`
  - `total_files>=1`
  - `dry_run=false`
  - `status_counter.failed=0`
  - `status_counter.partial=0`
  - `excel_written=true`
  - `output_exists=true`
  - `output_size_bytes>0`

This removes ambiguity in what counts as strong success evidence.

### 2) Hardened automation constraints and acceptance criteria

Updated automation task generation in `adapters/local_inbox_adapter.py`:

- added explicit constraint requiring wrapper success gating on the same
  delegate evidence fields
- added explicit acceptance criterion that wrapper success attestation must use
  those output-write and status-counter fields

This ensures the source contract enforces field-level semantics even when
runtime generation varies.

### 3) Added focused regression assertions

Updated `tests/test_local_inbox_adapter.py`:

- verifies `delegate_success_evidence` now includes explicit field-level
  attestation requirements
- verifies constraints include `excel_written=true` and
  `status_counter.partial=0` gating language
- verifies acceptance criteria include explicit output-write attestation clause

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-040` can be treated as complete as a source-side blocker-hardening
phase.

Generated wrapper success-evidence requirements are now explicit and
field-level in adapter guidance, reducing the chance of runtime overclaiming
success semantics.

Next required step: run a fresh same-origin governed validation to verify these
contract hardenings remove the runtime critic blocker observed in
`BL-20260325-039`.
