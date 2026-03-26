# Timeout Failover Production-Like Window Report

## Objective

Complete `BL-20260326-088` by validating timeout failover behavior in a
production-like provider-profile control path and archiving evidence that
separates endpoint/network timeout from prompt/schema outcomes.

## Scope

In scope:

- execute one governed replay using `ARGUS_PROVIDER_PROFILE` controls
- force primary endpoint timeout (`http_524`) and verify fallback endpoint
  recovery
- archive execute/runtime/state/request-trace artifacts

Out of scope:

- claims about real external provider SLA
- baseline retry/JSON budget changes

## Production-Like Profile Controls

Profile file:

- `runtime_archives/bl088/tmp/provider_profiles.bl088.json`

Profile used:

- `ARGUS_PROVIDER_PROFILE=bl088_production_like_failover`
- `ARGUS_PROVIDER_PROFILES_FILE=/Users/lingguozhong/openclaw-team/runtime_archives/bl088/tmp/provider_profiles.bl088.json`

Profile fields:

- `api_base=http://host.docker.internal:18083/v1` (primary)
- `fallback_chat_urls=[http://host.docker.internal:18084/v1/chat/completions]`
- `wire_api=chat_completions`
- `model_name=gpt-5-codex`
- `api_key_env=OPENAI_API_KEY_BL088`

Other controls:

- `ARGUS_LLM_MAX_RETRIES=2`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- `ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`

## Evidence

Primary outputs:

- `runtime_archives/bl088/tmp/bl088_profile_failover_summary.tsv`
- `runtime_archives/bl088/tmp/bl088_profile_failover_metrics.json`

Execute outputs:

- `runtime_archives/bl088/tmp/bl088_execute_replay_profile_failover.json`
- `runtime_archives/bl088/tmp/bl088_execute_replay_profile_failover.stderr.log`

Request traces:

- `runtime_archives/bl088/tmp/bl088_primary_requests.log`
- `runtime_archives/bl088/tmp/bl088_fallback_requests.log`

Runtime/state snapshots:

- `runtime_archives/bl088/runtime/automation-runtime.profile-failover.log`
- `runtime_archives/bl088/runtime/automation-output.profile-failover.json`
- `runtime_archives/bl088/runtime/critic-runtime.profile-failover.log`
- `runtime_archives/bl088/runtime/critic-output.profile-failover.json`
- `runtime_archives/bl088/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.profile-failover.json`
- `runtime_archives/bl088/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.profile-failover.json`

## Results

From `bl088_profile_failover_metrics.json`:

- status: `done`
- processed: `1`
- rejected: `0`
- critic verdict: `pass`
- automation status: `success`
- primary hits: `2`
- fallback hits: `2`
- automation failover markers: `2`
- critic failover markers: `2`

Separation signal is explicit:

- endpoint/network path: both workers show `class=http_524` on primary endpoint
- recovery path: both workers retry to configured fallback endpoint
- prompt/schema path: fallback payload remains contract-valid and finishes
  `processed/pass`, with no terminal JSON-invalid signal

## Decision

Production-like provider-profile failover behavior is validated for this
governed window:

- timeout-path failover works under provider-profile controls (not direct ad-hoc
  endpoint env wiring)
- baseline defaults remain unchanged

## Outcome

`BL-20260326-088` objective is achieved:

- production-like provider-profile failover window is archived
- timeout/network failures are cleanly distinguished from prompt/schema outcomes
- execution remains stable (`processed=1`, `critic_verdict=pass`)
