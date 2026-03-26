# Timeout Failover Stability Window Report

## Objective

Complete `BL-20260326-089` by quantifying short-window stability of
production-like provider-profile failover behavior across multiple governed
runs.

## Scope

In scope:

- run a 4-sample production-like failover matrix under fixed profile controls
- measure recovery stability, verdict quality, and wall-time spread
- derive reliability criteria for operational playbook readiness

Out of scope:

- external provider SLA claims
- baseline retry/JSON budget changes

## Controlled Setup

Profile controls:

- profile file: `runtime_archives/bl089/tmp/provider_profiles.bl089.json`
- profile name: `bl089_production_like_failover`
- primary `api_base=http://host.docker.internal:18085/v1`
- fallback `fallback_chat_urls=[http://host.docker.internal:18086/v1/chat/completions]`
- `wire_api=chat_completions`

Runtime controls:

- `ARGUS_LLM_MAX_RETRIES=2`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`

Sequence:

- `s01`, `s02`, `s03`, `s04`

## Evidence

Primary matrix and metrics:

- `runtime_archives/bl089/tmp/bl089_profile_failover_stability_matrix.tsv`
- `runtime_archives/bl089/tmp/bl089_profile_failover_stability_metrics.json`

Per-run artifacts:

- `runtime_archives/bl089/tmp/bl089_execute_replay_s*.json`
- `runtime_archives/bl089/runtime/*s*.log|json`
- `runtime_archives/bl089/state/*s*.json`
- `runtime_archives/bl089/tmp/bl089_primary_requests.s*.log`
- `runtime_archives/bl089/tmp/bl089_fallback_requests.s*.log`

## Results

From `bl089_profile_failover_stability_matrix.tsv`:

- `s01`: done, processed `1`, verdict `pass`, failover markers `2/2`
- `s02`: done, processed `1`, verdict `pass`, failover markers `2/2`
- `s03`: done, processed `1`, verdict `pass`, failover markers `2/2`
- `s04`: done, processed `1`, verdict `pass`, failover markers `2/2`

From `bl089_profile_failover_stability_metrics.json`:

- sample size: `4`
- processed: `4/4` (`100%`)
- rejected: `0/4` (`0%`)
- pass verdict rate: `100%`
- automation success rate: `100%`
- complete failover signal rate: `100%`
- automation wall seconds: avg `1.365`, min `1.335`, max `1.400`
- critic wall seconds: avg `1.333`, min `1.314`, max `1.349`

## Reliability Criteria (This Window)

For short-window playbook readiness, this run supports the following criteria:

1. `processed_rate >= 0.75`
2. `pass_verdict_rate >= 0.75`
3. `complete_failover_signal_rate >= 0.75`
4. no terminal JSON-invalid failures in the same window

BL-089 observed values exceed these thresholds (`1.0` across criteria).

## Decision

Timeout failover recovery appears stable in this short production-like window
under fixed provider-profile controls. Baseline defaults remain unchanged.

## Outcome

`BL-20260326-089` objective is achieved:

- multi-run stability is quantified and archived
- operational reliability criteria are recorded with evidence-backed thresholds
