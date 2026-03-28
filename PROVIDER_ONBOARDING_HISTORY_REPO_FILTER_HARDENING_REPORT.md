# Provider Onboarding History Repo-Filter Hardening Report

## Objective

Prevent non-repo temporary artifacts from distorting onboarding trend summaries.

## Scope

In scope:

- add repo-path filtering to history summary generation
- make gate-triggered summary refresh use repo-only filtering by default
- keep explicit opt-out for special non-repo scenarios

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- history summary filter hardening:
  - `scripts/provider_onboarding_history_summary.py`
- gate integration and controls:
  - `scripts/provider_onboarding_gate.py`
- test coverage:
  - `tests/test_provider_onboarding_history_summary.py`
  - `tests/test_provider_onboarding_gate.py`
- runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
- refreshed summary artifact:
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

## Validation Evidence

- repo-only summary now records dropped non-repo rows explicitly:
  - `dropped_non_repo_entries` field in
    `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
- gate tests verify default `--repo-only` pass-through and explicit opt-out:
  - `tests/test_provider_onboarding_gate.py`
- summary tests verify non-repo filtering behavior:
  - `tests/test_provider_onboarding_history_summary.py`

## Result

Onboarding trend summary is now protected against temp-path noise by default,
while retaining an explicit escape hatch when non-repo evidence is intentional.

## Decision

BL-099 remains blocked by provider onboarding availability; local evidence
quality is further hardened for stable longitudinal tracking.
