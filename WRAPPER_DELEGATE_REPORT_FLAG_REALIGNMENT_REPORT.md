# Wrapper Delegate Report-Flag Realignment Report

## Objective

Complete `BL-20260325-032` by hardening source-side generation contract rules so
future generated wrappers are less likely to drift from reviewed delegate CLI
report-handoff semantics and discovery behavior.

## Scope

In scope:

- tighten local inbox automation contract hints/constraints/acceptance criteria
- encode explicit report-flag compatibility requirements
- encode wrapper/delegate PDF discovery consistency requirements
- add/update focused regression coverage

Out of scope:

- fresh governed live Trello validation run
- branch-protection or governance policy changes
- git finalization / Trello Done writeback

## Changes

### 1) Added explicit report-flag compatibility guidance

Updated `adapters/local_inbox_adapter.py` contract hints with:

- `delegate_report_flag_contract`:
  requires using reviewed delegate flag `--report-json` (or explicitly
  supported alias), and explicitly warns against undeclared drift such as
  `--report-file`.

### 2) Added explicit discovery-consistency guidance

Updated contract hints with:

- `pdf_discovery_consistency`:
  wrapper preflight PDF discovery semantics must align with delegate discovery
  semantics (for example recursive vs non-recursive) to keep evidence counts
  consistent.

### 3) Strengthened constraints and acceptance criteria

Updated automation constraints to require:

- report sidecar handoff uses `--report-json` unless reviewed delegate supports
  another alias
- wrapper/delegate discovery semantics remain aligned

Updated acceptance criteria to require:

- wrapper/delegate sidecar handoff remains CLI-compatible with reviewed delegate
  flag contract
- wrapper preflight and delegate discovery semantics remain aligned

### 4) Focused regression update

Updated `tests/test_local_inbox_adapter.py` assertions to verify:

- new contract hints
  (`delegate_report_flag_contract`, `pdf_discovery_consistency`)
- new constraints for report-flag and discovery alignment
- new acceptance criteria for report-flag compatibility and discovery parity

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 -m unittest -v tests/test_trello_readonly_ingress.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-032` can be treated as complete as a source-side hardening phase.

The contract now explicitly blocks the specific wrapper report-flag drift seen
in `BL-20260325-031` and adds discovery-consistency guardrails.

Next required step: one fresh same-origin governed validation run to verify
runtime artifact generation and critic outcomes under the strengthened contract.
