# Wrapper Partial-Evidence Semantics Hardening Report

## Objective

Complete `BL-20260325-046` by hardening source-side wrapper contract guidance so
best-effort evidence-backed `partial` outcomes are treated as first-class
reviewable states (not implicitly escalated to `failed`) while preserving strict
anti-overclaim gates for wrapper `success` claims.

## Scope

In scope:

- update local inbox automation contract hints for success-vs-partial semantics
- update wrapper constraints/acceptance criteria to require explicit limitations
  and next-step guidance for contract-compliant partial outcomes
- focused regression coverage for the updated guidance text

Out of scope:

- live governed rerun in this phase
- changes to worker runtime retry implementation
- changes to external endpoint credentials/network conditions

## Changes

### 1) Refined wrapper success-vs-partial guidance

Updated `adapters/local_inbox_adapter.py`:

- strengthened `delegate_success_evidence` hint to clarify that strict evidence
  gates apply when wrapper status is `success`
- added new `delegate_partial_evidence` hint requiring:
  - contract-compliant delegate `partial` evidence to remain wrapper `partial`
  - no escalation to `failed` solely because success-only gates are unmet
  - explicit limitations and next-step guidance in wrapper output

### 2) Strengthened policy text in constraints and acceptance criteria

Updated automation task contract text in `adapters/local_inbox_adapter.py`:

- added explicit constraint requiring wrapper to keep evidence-backed partial
  outcomes as `partial` and include next-step guidance
- added explicit acceptance criterion that contract-compliant `partial`
  outcomes must not be escalated to `failed` by success-only gates

### 3) Added focused regression assertions

Updated `tests/test_local_inbox_adapter.py`:

- extended contract-hint assertions to cover new partial-evidence guidance
- added checks for new constraint and acceptance-criteria text ensuring
  success-vs-partial semantics remain explicit and enforced

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-046` can be treated as complete as a source-side blocker-hardening
phase.

The local inbox contract now explicitly preserves honest, reviewable `partial`
outcomes while keeping strict evidence requirements for wrapper `success`
claims.

Next required step: run a fresh same-origin governed validation to verify that
updated source-side semantics reduce recurrence of critic findings under real
execute conditions.
