# Provider Onboarding Gate Summary Refresh Report

## Objective

Remove manual drift between onboarding gate history and summary snapshot by
refreshing summary JSON automatically in the one-shot gate flow.

## Scope

In scope:

- auto-refresh history summary after gate history append
- keep explicit opt-out flag for controlled tests (`--no-history-summary`)
- refresh current local evidence snapshot

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- gate wrapper update:
  - `scripts/provider_onboarding_gate.py`
- test coverage update:
  - `tests/test_provider_onboarding_gate.py`
- runbook sync:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- refreshed evidence:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

## Validation Evidence

- latest gate assessment remains blocked:
  - `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json`
- summary now refreshes as part of gate run and shows latest blocked reason
  (`mixed_with_tls_transport_failures`):
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
- unit tests cover default refresh path and opt-out path:
  - `tests/test_provider_onboarding_gate.py`

## Result

One-shot onboarding gate now keeps history and summary synchronized by default.
Current status remains blocked (no `2xx` handshake path), with mixed auth/policy
and TLS transport signals captured.

## Decision

BL-099 remains blocked on usable provider/base+key onboarding input. Local
hardening for deterministic evidence continuity is complete for this increment.
