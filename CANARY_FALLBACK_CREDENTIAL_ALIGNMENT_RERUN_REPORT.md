# Canary Fallback Credential Alignment Rerun Report

## Objective

Execute `BL-20260326-092` by restoring fallback credential/profile availability
after BL-091 rollback, then rerun a guarded real-endpoint canary window and
check whether promotion thresholds are recovered.

## Scope

In scope:

- apply fallback key/profile alignment for real-endpoint failover path
- verify fallback endpoint preflight status code availability
- run a 4-sample rerun window (`s01..s04`) with execute/runtime/state evidence
- compute governed metrics and rollback decision

Out of scope:

- endpoint provider SLA claims
- baseline retry/JSON-budget uplift

## Controlled Setup

Profile controls (`runtime_archives/bl092/tmp/provider_profiles.bl092.json`):

- primary: `https://aixj.vip/v1/responses`
- fallback candidates:
  - `https://fast.vpsairobot.com/responses`
  - `https://fast.vpsairobot.com/v1/responses`
- `api_key_env=OPENAI_API_KEY_PRIMARY`
- `fallback_api_key_env=OPENAI_API_KEY_BL092`

Runtime controls:

- `ARGUS_PROVIDER_PROFILE=bl092_real_failover_canary_fixed`
- `ARGUS_PROVIDER_PROFILES_FILE=runtime_archives/bl092/tmp/provider_profiles.bl092.json`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- no default budget uplift

## Preflight Probe

Saved at `runtime_archives/bl092/tmp/bl092_probe_matrix.tsv`:

- `https://aixj.vip/v1/responses` (primary key) -> `502`
- `https://fast.vpsairobot.com/v1/responses` (fallback key) -> `200`
- `https://fast.vpsairobot.com/responses` (fallback key) -> `200`

Interpretation:

- fallback credential/profile availability is restored in preflight (`200`)
- primary path remains degraded (`502`) in this window

## Rerun Evidence

Primary matrix and metrics:

- `runtime_archives/bl092/tmp/bl092_canary_rerun_matrix.tsv`
- `runtime_archives/bl092/tmp/bl092_canary_rerun_metrics.json`

Per-sample artifacts:

- `runtime_archives/bl092/tmp/bl092_execute_replay_s*.json`
- `runtime_archives/bl092/runtime/automation-runtime.s*.log`
- `runtime_archives/bl092/runtime/automation-output.s*.json`
- `runtime_archives/bl092/state/*s*.json`

## Results

From `bl092_canary_rerun_metrics.json`:

- sample size: `4`
- processed: `1`
- rejected: `3`
- processed rate: `0.25`
- pass verdict rate: `0.25`
- complete failover signal rate: `1.0`
- observed automation error classes:
  - `workspace_missing_repo`
  - `http_502`
- rollback triggered: `true`

From `bl092_canary_rerun_matrix.tsv`:

- `s01` processed with `critic_verdict=pass`
- `s02` rejected with automation `workspace_missing_repo`
- `s03` rejected with terminal `http_502` exhaustion
- `s04` rejected with automation `workspace_missing_repo`

## Rollback Criteria Evaluation

Guardrails (any one triggers rollback):

1. terminal rejection present
2. `processed_rate < 0.75`
3. `pass_verdict_rate < 0.75`

Observed window hits all three, so rollback remains active.

## Decision

`BL-20260326-092` is **not cleared**.

What is validated:

- fallback credential/profile availability recovered to preflight `200`
- failover markers remain observable in runtime logs

What still blocks promotion:

- canary target thresholds were not met (`processed/pass = 0.25/0.25`)
- residual instability includes non-deterministic `workspace_missing_repo`
  failures plus persistent primary-path `http_502` terminal failures

## Next Blocker

Activate follow-up blocker:

- `BL-20260326-093` (`issue #178`) to stabilize workspace mount/runtime
  consistency and recover canary success rates under the same guarded controls.
