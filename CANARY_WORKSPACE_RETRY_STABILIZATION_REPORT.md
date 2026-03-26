# Canary Workspace-Retry Stabilization Report

## Objective

Execute `BL-20260326-093` by adding targeted retry hardening for
workspace-presence failure signatures in approved-preview automation execution,
then rerun a governed 4-sample real-endpoint canary window.

## Scope

In scope:

- add bounded workspace-presence retry guardrail in execute path
- add unit coverage for new retry condition
- rerun real-endpoint canary window (`s01..s04`) with full evidence
- evaluate rollback thresholds

Out of scope:

- baseline retry/JSON default uplift
- provider SLA claim

## Implementation

Code changes:

- `skills/execute_approved_previews.py`
  - added workspace-presence failure detection
  - added bounded retry budget for workspace-presence failures
    (`ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS`, default `1`)
  - sidecar/result now records `automation_workspace_retries_used`
- `tests/test_execute_approved_previews.py`
  - added regression test for workspace-presence retry path

Local validation:

- `python3 -m unittest tests.test_execute_approved_previews`
- `python3 -m unittest tests.test_execute_approved_previews tests.test_argus_hardening`

## Controlled Setup

Profile controls (`runtime_archives/bl093/tmp/provider_profiles.bl093.json`):

- primary: `https://aixj.vip/v1/responses`
- fallback:
  - `https://fast.vpsairobot.com/responses`
  - `https://fast.vpsairobot.com/v1/responses`
- split-key config:
  - `api_key_env=OPENAI_API_KEY_PRIMARY`
  - `fallback_api_key_env=OPENAI_API_KEY_BL093`

Runtime controls:

- `ARGUS_PROVIDER_PROFILE=bl093_real_failover_canary_stabilized`
- `ARGUS_PROVIDER_PROFILES_FILE=runtime_archives/bl093/tmp/provider_profiles.bl093.json`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS=1`

## Probe Evidence

Saved at `runtime_archives/bl093/tmp/bl093_probe_matrix.tsv`:

- `https://aixj.vip/v1/responses` -> `502`
- `https://fast.vpsairobot.com/responses` -> `200`
- `https://fast.vpsairobot.com/v1/responses` -> `200`

## Canary Rerun Evidence

Primary matrix and metrics:

- `runtime_archives/bl093/tmp/bl093_canary_window_matrix.tsv`
- `runtime_archives/bl093/tmp/bl093_canary_window_metrics.json`

Per-run snapshots:

- `runtime_archives/bl093/tmp/bl093_execute_replay_s*.json`
- `runtime_archives/bl093/runtime/automation-runtime.s*.log`
- `runtime_archives/bl093/runtime/automation-output.s*.json`
- `runtime_archives/bl093/state/*s*.json`

## Results

From `bl093_canary_window_metrics.json`:

- sample size: `4`
- processed: `0`
- rejected: `4`
- processed rate: `0.0`
- pass verdict rate: `0.0`
- complete failover signal rate: `1.0`
- observed automation error classes: `http_502`
- workspace retry used samples: `0`
- rollback triggered: `true`

Observed behavior:

- failover path markers remained observable (`next_endpoint=fast...`)
- window failures were endpoint-chain dominant:
  - primary `http_502`
  - fallback timeout chain
  - terminal return to primary `http_502`
- `workspace_missing_repo` class was not reproduced in this window

## Rollback Evaluation

Rollback guardrails (any one):

1. terminal rejection present
2. `processed_rate < 0.75`
3. `pass_verdict_rate < 0.75`

All three guardrails were hit.

## Decision

`BL-20260326-093` is **not cleared**.

Current status:

- workspace-retry hardening is implemented and unit-tested
- this real-endpoint window remains blocked by endpoint-side instability,
  not by workspace-presence drift

Next blocker:

- `BL-20260326-094` (`issue #180`) for endpoint-chain recovery under the same
  guarded canary thresholds.
