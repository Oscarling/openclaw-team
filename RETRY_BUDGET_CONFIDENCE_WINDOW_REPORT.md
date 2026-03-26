# Retry Budget Confidence Window Report

## Objective

Complete `BL-20260326-081` by extending the governed replay sample window with
time-spread alternating runs (`budget=1` vs `budget=2`), then decide whether
default retry-budget guidance should change.

## Scope

In scope:

- run 4 governed replay samples with fixed controls and alternating budgets
- compare BL-081 local outcomes and BL-080+BL-081 combined outcomes
- decide whether default guidance remains `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`

Out of scope:

- provider-side SLA remediation
- large-sample statistical inference

## Controlled Setup

Shared controls:

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- execute command:
  - `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Variable under test:

- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS` in `{1, 2}`

BL-081 time-spread sequence:

- `s01-b1`, `s02-b2`, `s03-b1`, `s04-b2`

## Evidence

Primary BL-081 matrix:

- `runtime_archives/bl081/tmp/bl081_time_spread_matrix.tsv`

Prior BL-080 matrix used for combined confidence window:

- `runtime_archives/bl080/tmp/bl080_budget_tradeoff_matrix.tsv`

BL-081 runtime/state archive:

- `runtime_archives/bl081/runtime/*`
- `runtime_archives/bl081/state/*`
- `runtime_archives/bl081/tmp/bl081_execute_replay_s*-b*.json`

## Results

### BL-081 raw outcomes

- `s01-b1`: rejected, retries_used `1`, wall `241s`, `auto_error_class=timeout`
- `s02-b2`: rejected, retries_used `2`, wall `362s`, `auto_error_class=timeout`
- `s03-b1`: rejected, retries_used `1`, wall `241s`, `auto_error_class=timeout`
- `s04-b2`: processed, retries_used `0`, wall `116s`, `critic_verdict=pass`

### BL-081 aggregated

- `budget=1` (2 runs):
  - pass-rate (`processed`) = `0/2 = 0%`
  - avg wall time = `241.0s`
  - avg retries used = `1.00`
- `budget=2` (2 runs):
  - pass-rate (`processed`) = `1/2 = 50%`
  - avg wall time = `239.0s`
  - avg retries used = `1.00`

### Combined BL-080 + BL-081 confidence window

Combined sample size: `8` runs (`budget=1`: 4 runs, `budget=2`: 4 runs).

- `budget=1` (4 runs):
  - pass-rate (`processed`) = `0/4 = 0%`
  - avg wall time = `207.5s`
  - avg retries used = `0.75`
  - automation error class distribution = `timeout: 3`, `none: 1`
- `budget=2` (4 runs):
  - pass-rate (`processed`) = `1/4 = 25%`
  - avg wall time = `275.8s`
  - avg retries used = `1.50`
  - automation error class distribution = `timeout: 2`, `none: 2`

Latency delta (`budget=2` vs `budget=1`, combined window):

- `+68.3s` average wall time (`207.5s -> 275.8s`)
- relative increase `+32.9%`

## Decision

Guidance remains unchanged:

- keep default `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`

Rationale:

- combined window shows only limited pass-rate improvement for `budget=2`
  (`25%`, `1/4`) with small sample size and unstable verdict mix
- `budget=2` still carries material latency and retry cost increases
  (`+32.9%` wall, `2x` average retries vs budget `1`)
- evidence is sufficient to avoid changing default baseline, while preserving
  `budget=2` as a controlled temporary override path

Operational note:

- use `budget=2` only in explicit, short-lived recovery windows for priority
  replays; keep baseline/default at `1`.

## Outcome

`BL-20260326-081` objective is achieved:

- extended time-spread replay evidence is archived
- combined confidence-window comparison is documented
- default retry-budget guidance remains frozen at `1`
