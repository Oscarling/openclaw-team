# Provider Onboarding History Summary Automation Report

## Objective

Automate trend summarization for onboarding gate history, so the latest blocked
state and reason distribution are available in one machine-readable snapshot.

## Scope

In scope:

- add history summary script for JSONL history
- produce status/reason/exit-code counters plus latest snapshot
- add dedicated unit tests and premerge integration

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- script:
  - `scripts/provider_onboarding_history_summary.py`
- tests:
  - `tests/test_provider_onboarding_history_summary.py`
- merge gate update:
  - `scripts/premerge_check.sh`
- summary artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary_20260328.json`

## Result

Current summary confirms:

- `entry_count=1`
- latest `status=blocked`
- latest `block_reason=auth_or_access_policy_block`

## Decision

History summary automation is complete and can be regenerated after each gate
run to track onboarding trend changes.
