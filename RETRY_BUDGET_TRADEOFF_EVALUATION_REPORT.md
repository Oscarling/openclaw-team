# Retry Budget Tradeoff Evaluation Report

## Objective

Complete `BL-20260326-080` by quantifying pass-rate and latency tradeoff between
transient retry budgets `1` and `2` under the repo-baseline governed replay
profile, then freeze recommended default/profile guidance.

## Scope

In scope:

- controlled governed replay samples for `budget=1` and `budget=2`
- compare pass-rate and wall-time impact
- freeze run guidance for `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS`

Out of scope:

- provider-side SLA remediation
- large-sample statistical confidence claims

## Controlled Setup

Shared runtime controls across all samples:

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset (repo baseline file)
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- execute command:
  - `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Variable under test:

- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS` in `{1, 2}`

## Evidence

Primary matrix:

- `runtime_archives/bl080/tmp/bl080_budget_tradeoff_matrix.tsv`

Per-run runtime/state archives:

- `runtime_archives/bl080/runtime/*`
- `runtime_archives/bl080/state/*`
- `runtime_archives/bl080/tmp/bl080_execute_replay_b*-run*.json`

## Results

### Raw run outcomes

From `bl080_budget_tradeoff_matrix.tsv`:

- `budget=1, run01`: rejected, wall `107s`, retries_used `0`, automation `success`, final `critic_verdict=needs_revision`
- `budget=1, run02`: rejected, wall `241s`, retries_used `1`, automation failed on `timeout`
- `budget=2, run01`: rejected, wall `250s`, retries_used `2`, automation failed on `timeout`
- `budget=2, run02`: rejected, wall `375s`, retries_used `2`, automation `success`, final `critic_verdict=fail`

### Aggregated comparison

- `budget=1` (2 runs):
  - pass-rate (`processed`) = `0/2 = 0%`
  - avg wall time = `174.0s`
  - avg retries used = `0.50`
- `budget=2` (2 runs):
  - pass-rate (`processed`) = `0/2 = 0%`
  - avg wall time = `312.5s`
  - avg retries used = `2.00`

Latency delta:

- `budget=2` vs `budget=1` average wall-time increase:
  - `+138.5s` (from `174.0s` to `312.5s`)
  - relative increase `+79.6%`

## Decision (Guidance Freeze)

Freeze recommendation:

- keep default `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- do **not** raise default to `2` based on current evidence window

Rationale:

- no observed pass-rate gain (`0%` vs `0%`) in this controlled sample
- substantial latency penalty when budget is raised (`+79.6%` avg wall time)

Operational guidance:

- `budget=2` may still be used as an explicit temporary override in a controlled
  recovery window, but should not be adopted as baseline default without fresh
  evidence showing clear pass-rate improvement.

## Outcome

`BL-20260326-080` objective is achieved:

- controlled sample evidence compares budgets `1` and `2`
- pass-rate/latency tradeoff is archived
- default/profile guidance is now frozen to keep default budget at `1`

## Next Blocker

Queue `BL-20260326-081`:

- collect a larger time-window sample (same controls) to verify whether there
  are periodic provider conditions where temporary budget `2` yields meaningful
  pass-rate gains that justify higher latency.
