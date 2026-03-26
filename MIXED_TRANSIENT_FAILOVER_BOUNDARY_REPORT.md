# Mixed Transient Failover Boundary Report

## Objective

Complete `BL-20260326-090` by validating failover boundary behavior under mixed
transient classes and one fallback degradation scenario, then codify rollback
triggers for operational playbooks.

## Scope

In scope:

- run a governed 4-scenario matrix under provider-profile failover controls
- cover primary transient classes: `http_524`, `http_502`, `timeout`
- include at least one fallback degradation case
- quantify outcome boundaries and define rollback triggers

Out of scope:

- external provider SLA claims
- baseline retry/JSON budget changes

## Controlled Setup

Profile controls:

- profile file: `runtime_archives/bl090/tmp/provider_profiles.bl090.json`
- profile name: `bl090_mixed_failover`
- primary: `http://host.docker.internal:18087/v1`
- fallback: `http://host.docker.internal:18088/v1/chat/completions`

Runtime controls:

- `ARGUS_LLM_TIMEOUT_SECONDS=1`
- `ARGUS_LLM_MAX_RETRIES=2`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`

Scenario matrix:

- `s01`: primary `http_524`, fallback `success`
- `s02`: primary `http_502`, fallback `success`
- `s03`: primary `timeout`, fallback `success`
- `s04`: primary `http_524`, fallback `http_502` (degradation boundary)

## Evidence

Primary matrix and metrics:

- `runtime_archives/bl090/tmp/bl090_mixed_failover_boundary_matrix.tsv`
- `runtime_archives/bl090/tmp/bl090_mixed_failover_boundary_metrics.json`

Scenario definitions:

- `runtime_archives/bl090/tmp/bl090_scenarios.tsv`

Per-run artifacts:

- `runtime_archives/bl090/tmp/bl090_execute_replay_s*.json`
- `runtime_archives/bl090/runtime/*s*.log|json`
- `runtime_archives/bl090/state/*s*.json`
- `runtime_archives/bl090/tmp/bl090_primary_requests.s*.log`
- `runtime_archives/bl090/tmp/bl090_fallback_requests.s*.log`

## Results

From `bl090_mixed_failover_boundary_metrics.json`:

- sample size: `4`
- processed: `3`
- rejected: `1`
- processed rate: `0.75`
- pass verdict rate: `0.75`
- observed automation error classes:
  - `http_524`
  - `http_502`
  - `timeout`
- degraded fallback cases: `1`
- degraded fallback rejected cases: `1`
- degraded fallback rejected rate: `1.0`

Boundary behavior:

- success scenarios (`s01/s02/s03`) all recovered through fallback and ended
  `processed=1`, `critic_verdict=pass`
- degradation scenario (`s04`) produced fail-closed rejection with terminal
  fallback error `class=http_502` as expected

## Rollback Triggers

For operational failover playbooks, trigger rollback/escalation when either
condition is met in a short window:

1. any degraded-fallback scenario yields terminal rejection (`rejected>0`)
2. failover path cannot maintain at least `processed_rate >= 0.75` and
   `pass_verdict_rate >= 0.75`

## Decision

Mixed-class boundary behavior is now quantified and consistent with safety
expectation:

- failover recovers primary transient faults across multiple classes
- degraded fallback path fails closed and is detectable via explicit markers

## Outcome

`BL-20260326-090` objective is achieved:

- mixed transient + degraded fallback boundary evidence is archived
- rollback trigger conditions are explicit for operational playbooks
