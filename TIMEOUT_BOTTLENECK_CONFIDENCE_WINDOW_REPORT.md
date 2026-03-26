# Timeout Bottleneck Confidence Window Report

## Objective

Complete `BL-20260326-086` by quantifying timeout-dominant failure concentration
across governed replay windows, then codify mitigation priority in runtime
guidance.

## Scope

In scope:

- aggregate archived governed replay evidence from BL-080/081/083/084/085
- quantify timeout share among failed rows and overall sample
- confirm whether terminal JSON-invalid remains a meaningful failure class
- freeze mitigation priority guidance based on measured distribution

Out of scope:

- introducing new provider credentials or endpoints
- changing default retry/JSON-repair budgets

## Evidence Inputs

Source matrices:

- `runtime_archives/bl080/tmp/bl080_budget_tradeoff_matrix.tsv`
- `runtime_archives/bl081/tmp/bl081_time_spread_matrix.tsv`
- `runtime_archives/bl083/tmp/bl083_replay_summary.tsv`
- `runtime_archives/bl084/tmp/bl084_json_repair_confidence_matrix.tsv`
- `runtime_archives/bl085/tmp/bl085_controlled_replay_summary.tsv`

BL-086 aggregated outputs:

- `runtime_archives/bl086/tmp/bl086_timeout_bottleneck_summary.tsv`
- `runtime_archives/bl086/tmp/bl086_timeout_bottleneck_metrics.json`

## Aggregated Results

From `bl086_timeout_bottleneck_metrics.json`:

- sample size: `14`
- processed: `3`
- rejected: `11`
- processed rate: `21.43%`
- failed rows: `11`
- timeout failed rows: `9`
- timeout share among failures: `81.82%`
- timeout share overall: `64.29%`
- terminal JSON-invalid rows: `0`
- terminal JSON-invalid rate: `0%`
- average wall time: `238.0s`
- failed error-class distribution:
  - `timeout`: `9`
  - `none`: `2`

## Interpretation

- Timeout remains the dominant failure class by a large margin in governed
  windows after retry-budget and JSON-repair hardening work.
- JSON-validity terminal failures are currently absent in this confidence
  window (`0/14`), consistent with BL-083/084/085 evidence that JSON path is no
  longer the primary blocker.
- Current reliability uplift is more likely to come from timeout-path mitigation
  (provider latency/availability handling and failover governance) than from
  increasing JSON repair or transient retry defaults.

## Decision

Guidance freeze:

- keep baseline defaults:
  - `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
  - `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`
- when failures are timeout-dominant, prioritize timeout mitigation work before
  tuning JSON-path budgets.

## Outcome

`BL-20260326-086` objective is achieved:

- cross-window timeout concentration is quantified with archived evidence
- runtime guidance now explicitly prioritizes timeout-path mitigation under
  timeout-dominant windows
