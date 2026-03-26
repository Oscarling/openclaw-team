# JSON Repair Engagement Confidence Window Report

## Objective

Complete `BL-20260326-084` by quantifying real-run engagement frequency of
`json_output_repair_attempts_used` across a time-spread governed replay window,
and checking whether the JSON-repair guardrail introduces observable quality or
latency regression signals under baseline controls.

## Scope

In scope:

- run a 4-sample time-spread governed replay matrix under fixed baseline controls
- measure:
  - JSON-repair engagement frequency (`json_output_repair_attempts_used`)
  - terminal JSON-invalid failures (`LLM output not valid JSON`)
  - verdict and wall-time characteristics
- update run guidance based on observed confidence window

Out of scope:

- provider-side timeout SLA remediation
- raising baseline transient retry budget

## Controlled Setup

Shared controls for all BL-084 samples:

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1` (baseline)
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1` (bounded repair default)

Sequence:

- `s01-baseline`, `s02-baseline`, `s03-baseline`, `s04-baseline`

## Evidence

Primary matrix:

- `runtime_archives/bl084/tmp/bl084_json_repair_confidence_matrix.tsv`

Per-run artifacts:

- `runtime_archives/bl084/tmp/bl084_execute_replay_s*-baseline.json`
- `runtime_archives/bl084/runtime/*s*-baseline*`
- `runtime_archives/bl084/state/*s*-baseline*`

## Results

### Raw outcomes

From `bl084_json_repair_confidence_matrix.tsv`:

- `s01`: rejected, `critic_verdict=needs_revision`, `json_repair_used=0`, wall `241s`, terminal class `timeout` (automation)
- `s02`: rejected, `critic_verdict=needs_revision`, `json_repair_used=0`, wall `306s`, terminal class `timeout` (critic)
- `s03`: rejected, `critic_verdict=needs_revision`, `json_repair_used=0`, wall `242s`, terminal class `timeout` (automation)
- `s04`: rejected, `critic_verdict=needs_revision`, `json_repair_used=0`, wall `241s`, terminal class `timeout` (automation)

### Aggregated metrics

- sample size: `4`
- processed pass-rate: `0/4 = 0%`
- avg wall-time: `257.5s`
- avg transient retries used: `1.00`
- JSON-repair engagement rate:
  - runs with `json_repair_used > 0`: `0/4 = 0%`
- terminal JSON-invalid failure rate:
  - `json_invalid_terminal=yes`: `0/4 = 0%`
- dominant terminal class: `timeout` (`4/4`)

## Decision

Guidance remains unchanged:

- keep `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1` (bounded default)
- keep `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1` baseline default

Interpretation:

- in this confidence window, JSON-repair path engagement was `0%` and no run
  terminated on JSON-invalid output, which is consistent with BL-083 hardening
  expectation (no recurrence of terminal JSON-invalid path)
- current reliability bottleneck remains upstream timeout behavior rather than
  JSON validity handling
- no evidence in this window that JSON-repair guardrail regresses quality; the
  observed failures are timeout-dominant

## Outcome

`BL-20260326-084` objective is achieved:

- time-spread engagement frequency is measured and archived
- terminal JSON-invalid regressions are absent in the sampled window
- baseline guidance remains stable without drift
