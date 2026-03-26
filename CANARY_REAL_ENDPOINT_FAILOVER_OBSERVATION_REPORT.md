# Canary Real-Endpoint Failover Observation Report

## Objective

Complete `BL-20260326-091` by running a short canary-style observation window
against real endpoint topology, validating failover markers and enforcing
strict rollback guardrails without changing baseline defaults.

## Scope

In scope:

- run a 4-sample canary observation window on real upstream endpoints
- capture execute/runtime/state evidence for each sample
- measure processed/pass and failover marker outcomes
- apply explicit rollback criteria and produce an operational decision

Out of scope:

- provider SLA claims
- baseline retry or JSON budget uplift

## Controlled Setup

Profile controls:

- profile file: `runtime_archives/bl091/tmp/provider_profiles.bl091.json`
- profile name: `bl091_real_failover_canary`
- primary: `https://aixj.vip/v1/responses`
- fallback candidates:
  - `https://fast.vpsairobot.com/v1/responses`
  - `https://fast.vpsairobot.com/responses`

Runtime controls:

- `ARGUS_PROVIDER_PROFILE=bl091_real_failover_canary`
- `ARGUS_PROVIDER_PROFILES_FILE=runtime_archives/bl091/tmp/provider_profiles.bl091.json`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- no baseline default uplift on retry/json budget

Preflight probe snapshot (`bl091_probe_matrix.tsv`):

- `https://aixj.vip/v1/responses -> 502`
- `https://aixj.vip/responses -> 502`
- `https://fast.vpsairobot.com/v1/responses -> 401`
- `https://fast.vpsairobot.com/responses -> 401`

## Evidence

Primary matrix and metrics:

- `runtime_archives/bl091/tmp/bl091_canary_observation_matrix.tsv`
- `runtime_archives/bl091/tmp/bl091_canary_observation_metrics.json`

Topology probe:

- `runtime_archives/bl091/tmp/bl091_probe_matrix.tsv`

Per-run artifacts:

- `runtime_archives/bl091/tmp/bl091_execute_replay_s*.json`
- `runtime_archives/bl091/runtime/automation-runtime*.s*.log`
- `runtime_archives/bl091/runtime/automation-task.s*.json`
- `runtime_archives/bl091/runtime/automation-output.s*.json`
- `runtime_archives/bl091/state/*s*.json`

Representative runtime marker (`automation-runtime.s01.log`):

- primary failure `class=http_502` on `https://aixj.vip/v1/responses`
- failover attempt marker `next_endpoint=https://fast.vpsairobot.com/v1/responses`
- fallback authorization failure `class=http_401`
- terminal rejection after retry exhaustion returns to primary path

## Results

From `bl091_canary_observation_matrix.tsv`:

- `s01..s04`: all `rejected`
- `critic_verdict`: `needs_revision` in all samples (critic not reached)
- `automation_error_class`: `http_502` terminal in all samples
- automation failover marker observed in all samples (`4/4`)

From `bl091_canary_observation_metrics.json`:

- sample size: `4`
- processed: `0`
- rejected: `4`
- processed rate: `0.0`
- pass verdict rate: `0.0`
- complete failover signal rate: `1.0`
- observed automation error classes: `http_502`
- rollback triggered: `true`

## Rollback Criteria Evaluation

Rollback guardrail triggers (any one is sufficient):

1. terminal rejection present
2. `processed_rate < 0.75`
3. `pass_verdict_rate < 0.75`

Observed window hit all three triggers, so rollback/escalation is mandatory for
this canary.

## Decision

Canary observation confirms failover path markers are detectable on real
endpoints, and strict guardrails correctly force rollback when fallback
authorization is unavailable.

Operational decision:

- stop canary promotion for this topology
- treat credential/profile alignment on fallback path as the next blocker

## Outcome

`BL-20260326-091` objective is achieved as a governed canary decision point:

- real-topology failover markers were observed and archived
- rollback guardrails were enforced with explicit trigger evidence
- next action is a focused remediation blocker before any further canary window
