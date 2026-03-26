# Timeout Failover Drill Runbook Report

## Objective

Complete `BL-20260326-087` by validating timeout failover behavior through one
governed drill that forces primary endpoint timeout and confirms fallback-path
recovery with archived evidence.

## Scope

In scope:

- execute one controlled replay with a timeout-failing primary endpoint
- verify retry-to-fallback behavior in automation and critic runtime logs
- archive execute/runtime/state/request-trace evidence
- codify activation/rollback expectations for timeout failover drill usage

Out of scope:

- production endpoint health claims
- baseline default budget changes

## Controlled Setup

Replay command:

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Runtime controls:

- `OPENAI_API_BASE=http://host.docker.internal:18081/v1` (primary drill endpoint)
- `ARGUS_LLM_FALLBACK_CHAT_URLS=http://host.docker.internal:18082/v1/chat/completions`
- `ARGUS_LLM_WIRE_API=chat_completions`
- `ARGUS_LLM_MAX_RETRIES=2`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`
- `ARGUS_PROVIDER_PROFILE` unset

Drill endpoint behavior:

- primary endpoint always returns `HTTP 524`
- fallback endpoint returns contract-valid success payloads

## Evidence

Primary outputs:

- `runtime_archives/bl087/tmp/bl087_failover_drill_summary.tsv`
- `runtime_archives/bl087/tmp/bl087_failover_drill_metrics.json`

Execute outputs:

- `runtime_archives/bl087/tmp/bl087_execute_replay_failover.json`
- `runtime_archives/bl087/tmp/bl087_execute_replay_failover.stderr.log`

Request traces:

- `runtime_archives/bl087/tmp/bl087_primary_requests.log`
- `runtime_archives/bl087/tmp/bl087_fallback_requests.log`

Runtime/state snapshots:

- `runtime_archives/bl087/runtime/automation-runtime.failover.log`
- `runtime_archives/bl087/runtime/automation-output.failover.json`
- `runtime_archives/bl087/runtime/critic-runtime.failover.log`
- `runtime_archives/bl087/runtime/critic-output.failover.json`
- `runtime_archives/bl087/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.failover.json`
- `runtime_archives/bl087/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.failover.json`

## Results

From `bl087_failover_drill_metrics.json`:

- status: `done`
- processed: `1`
- rejected: `0`
- critic verdict: `pass`
- automation status: `success`
- primary hits: `2`
- fallback hits: `2`
- automation failover markers: `2`
- critic failover markers: `2`

Runtime log evidence confirms explicit failover sequence in both workers:

- first attempt fails with `class=http_524` on primary endpoint
- retry targets fallback endpoint `http://host.docker.internal:18082/v1/chat/completions`
- task then completes successfully

## Decision

Timeout failover drill behavior is validated under governance:

- timeout-path fallback routing works as expected for both automation and critic
- no baseline-default escalation is needed from this drill
- timeout failover remains a governed, evidence-backed mitigation path

## Outcome

`BL-20260326-087` objective is achieved:

- governed timeout failover drill is executed and archived
- failover path is confirmed with explicit runtime/request-trace evidence
- rollback-friendly baseline defaults remain unchanged
