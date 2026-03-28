# Project Delivery Status Board Report

## Objective

Provide a one-command, non-technical status board that explains where the
project currently stands, what remains blocked, and what to do next.

## Scope

In scope:

- parse `PROJECT_BACKLOG.md` and compute completion metrics
- summarize critical external dependency chain (`BL-092` to `BL-099`)
- read latest onboarding summary signal
- output deterministic JSON + Markdown status board
- add unit tests and premerge coverage
- document command usage in local runbook

Out of scope:

- changing provider/base routing behavior
- modifying replay/canary decision policies
- mutating backlog statuses automatically

## Deliverables

- new status script:
  - `scripts/project_delivery_status.py`
- new tests:
  - `tests/test_project_delivery_status.py`
- merge-gate integration:
  - `scripts/premerge_check.sh`
- operator runbook update:
  - `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`

## Validation Evidence

- script output includes:
  - `delivery_state`
  - `backlog.total/done/completion_percent/status_counts/phase_counts`
  - `critical_provider_chain` (`BL-092~BL-099`, clear/blockers)
  - `onboarding_latest`
  - `next_steps`
- `tests/test_project_delivery_status.py` covers:
  - blocked-external-provider state
  - ready-for-replay state
  - missing-summary unknown state
- `scripts/premerge_check.sh` now executes the new test module
- runbook includes reproducible command example with output paths

## Result

Operators can now explain progress and blockers with one deterministic command,
without manually cross-reading backlog entries and onboarding artifacts.

## Decision

This is a minimal, low-risk observability improvement focused on project
completion communication under ongoing external provider/base instability.
