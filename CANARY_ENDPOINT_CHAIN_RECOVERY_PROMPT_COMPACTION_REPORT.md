# Canary Endpoint-Chain Recovery Prompt-Compaction Report

## Objective

Execute `BL-20260326-094` with controlled prompt-shaping mitigation and rerun a
governed 4-sample real-endpoint canary window.

## Scope

In scope:

- add optional automation prompt-field compaction control
- keep default behavior unchanged when control is unset
- rerun real-endpoint canary window (`s01..s04`) with evidence
- evaluate rollback thresholds

Out of scope:

- provider SLA claim
- baseline timeout/retry budget uplift

## Implementation

Code changes:

- `dispatcher/worker_runtime.py`
  - added `ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS` parsing and guardrails
  - added `compact_prompt_text(...)`
  - `build_user_prompt(...)` now supports optional field compaction for
    `worker=automation` and appends `Prompt Compact Notes`
- `tests/test_argus_hardening.py`
  - added regression tests for default non-compaction path
  - added regression tests for env-driven compaction path
- `RUNTIME_CONTRACT.md`
  - added local-first staged-upload collaboration clause

Local validation:

- `python3 -m unittest tests.test_argus_hardening tests.test_execute_approved_previews`

## Controlled Setup

Profile controls (`runtime_archives/bl094/tmp/provider_profiles.bl094.json`):

- primary: `https://aixj.vip/v1/responses`
- fallback:
  - `https://fast.vpsairobot.com/responses`
  - `https://fast.vpsairobot.com/v1/responses`
- split-key config:
  - `api_key_env=OPENAI_API_KEY_PRIMARY`
  - `fallback_api_key_env=OPENAI_API_KEY_BL094`

Runtime controls:

- `ARGUS_PROVIDER_PROFILE=bl094_prompt_compact_canary`
- `ARGUS_PROVIDER_PROFILES_FILE=runtime_archives/bl094/tmp/provider_profiles.bl094.json`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS=1`
- `ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS=1200`

## Probe Evidence

Saved at `runtime_archives/bl094/tmp/bl094_probe_matrix.tsv`:

- `https://aixj.vip/v1/responses` -> `502`
- `https://fast.vpsairobot.com/responses` -> `200`
- `https://fast.vpsairobot.com/v1/responses` -> `200`

## Canary Rerun Evidence

Primary matrix and metrics:

- `runtime_archives/bl094/tmp/bl094_canary_observation_matrix.tsv`
- `runtime_archives/bl094/tmp/bl094_canary_observation_metrics.json`

Per-run snapshots:

- `runtime_archives/bl094/tmp/bl094_execute_replay_s*.json`
- `runtime_archives/bl094/runtime/automation-runtime.s*.log`
- `runtime_archives/bl094/runtime/automation-output.s*.json`
- `runtime_archives/bl094/state/*s*.json`

## Results

From `bl094_canary_observation_metrics.json`:

- sample size: `4`
- processed: `0`
- rejected: `4`
- processed rate: `0.0`
- pass verdict rate: `0.0`
- complete failover signal rate: `1.0`
- observed automation error classes: `http_502`, `remote_closed`
- rollback triggered: `true`

Observed behavior:

- failover path markers remained observable in all samples
- dominant failure chain stayed endpoint-side:
  - primary `http_502`
  - fallback `remote_closed`/timeout chain
  - terminal return to primary `http_502`
- one sample (`s03`) returned model-side failed summary
  (`repository files are not accessible`) under the same endpoint chain

Prompt compaction verification (local replay on captured task):

- baseline prompt chars: `13136`
- compacted prompt chars: `6505`
- reduction: `6631`
- truncation markers present:
  - `inputs: truncated to 1200 chars (original=5294)`
  - `constraints: truncated to 1200 chars (original=2985)`
  - `acceptance_criteria: truncated to 1200 chars (original=2121)`

## Rollback Evaluation

Rollback guardrails (any one):

1. terminal rejection present
2. `processed_rate < 0.75`
3. `pass_verdict_rate < 0.75`

All three guardrails were hit.

## Decision

`BL-20260326-094` is **not cleared** and remains **blocked**.

Current status:

- prompt compaction mitigation is implemented, bounded, and test-covered
- real-endpoint canary thresholds remain unachieved under the active topology
- dominant blocker remains endpoint-chain instability rather than prompt volume

Next blocker:

- `BL-20260326-095`: recover canary by isolating fallback `remote_closed` path
  and validating a stable provider/endpoint route under the same rollback
  guardrails.
