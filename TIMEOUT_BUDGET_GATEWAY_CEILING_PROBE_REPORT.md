# Timeout-Budget Gateway Ceiling Probe Report

## Objective

Execute `BL-20260326-098` timeout-budget probing on the current fast route to
verify whether increasing request timeout alone can recover real automation
prompt-shape execution.

## Scope

In scope:

- keep current provider topology unchanged (`fast.vpsairobot.com`)
- use real automation prompt shape from governed runtime evidence
- test timeout budgets `120/180/240/300` seconds under single-attempt settings
- determine whether any budget produces a stable success candidate

Out of scope:

- provisioning a new provider/base route
- full 4-sample canary promotion window

## Controlled Setup

Probe runner:

- `runtime_archives/bl098/tmp/bl098_timeout_budget_probe.py`

Input task source:

- `runtime_archives/bl094/runtime/automation-task.s01.json`

Runtime controls:

- endpoint: `https://fast.vpsairobot.com/v1/responses`
- model: `gpt-5-codex`
- prompt compaction: `ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS=1200`
- retries: `ARGUS_LLM_MAX_RETRIES=1`
- timeout-recovery retries: `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- timeout budgets: `120`, `180`, `240`, `300`

## Evidence

- timeout-budget matrix:
  - `runtime_archives/bl098/tmp/bl098_timeout_budget_probe.tsv`

## Results

Observed outcomes by budget:

- `120s`: terminal `timeout`, elapsed `121.702s`
- `180s`: terminal `http_524`, elapsed `125.866s`
- `240s`: terminal `http_524`, elapsed `125.902s`
- `300s`: terminal `http_524`, elapsed `125.882s`

No successful completion was observed, so no 4-sample repeat run was started.

## Interpretation

- Raising local timeout budget from `120` to `300` seconds did not unlock the
  route.
- The route shows an effective upstream gateway ceiling around `~126s`
  (`http_524`) for this real prompt shape.
- Current blocker remains route/topology-level rather than local timeout tuning.

## Decision

`BL-20260326-098` is **blocked** on current topology.

Next action gate:

- introduce a genuinely new provider/base route (new key/base topology), then
  rerun controlled replay before re-entering canary clearance.
