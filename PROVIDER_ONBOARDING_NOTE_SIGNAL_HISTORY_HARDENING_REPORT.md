# Provider Onboarding Note-Signal History Hardening Report

## Objective

Persist and summarize note-level handshake signals in onboarding history so trend
analysis can distinguish auth/policy/TLS classes, not just HTTP codes.

## Scope

In scope:

- persist `note_class_counts` in onboarding gate history rows
- aggregate `note_class_counts` in history summary snapshots
- extend schema/path validation for note-level counter shape
- keep consistency checks aware of new summary field

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- gate history enrichment:
  - `scripts/provider_onboarding_gate.py`
- summary aggregation update:
  - `scripts/provider_onboarding_history_summary.py`
- validator update:
  - `scripts/provider_onboarding_history_validate.py`
- consistency check update:
  - `scripts/provider_onboarding_history_consistency_check.py`
- tests:
  - `tests/test_provider_onboarding_gate.py`
  - `tests/test_provider_onboarding_history_summary.py`
  - `tests/test_provider_onboarding_history_validate.py`
  - `tests/test_provider_onboarding_history_consistency_check.py`
- refreshed summary artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

## Validation Evidence

- history rows can now carry note-level counts from assessment output
- summary JSON includes top-level aggregated `note_class_counts`
- validator rejects malformed note-level counters
- consistency check still passes against current repo artifacts

## Result

Onboarding evidence now preserves and surfaces note-level signal trends in a
machine-readable, merge-gated path.

## Decision

BL-099 remains externally blocked; local evidence fidelity improved with
signal-level continuity across history and summary.
