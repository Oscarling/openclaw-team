# Post Fast-Provider Timeout Stability Validation Report

## Objective

Validate `BL-20260325-074` by testing whether timeout-tuned governed replay can
clear terminal timeout/auth failures and reach automation success under aligned
fast-provider profile.

## Scope

In scope:

- two elevated governed replay runs with tuned timeout/model settings
- profile-selected runtime config only (no desktop extraction in execute step)
- evidence archival and blocker-class determination

Out of scope:

- multi-provider cross-key failover implementation
- provider-side SLA remediation

## Validation Runs

Target preview:

- `preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153`

### Run A (gpt-5.4 tuned)

- profile: `/tmp/bl074_provider_profiles.json`
- model: `gpt-5.4`
- env: `ARGUS_LLM_TIMEOUT_SECONDS=300`, `ARGUS_LLM_MAX_RETRIES=2`
- result artifact:
  - `runtime_archives/bl074/tmp/bl074_execute_replay_tuned.json`
- outcome:
  - `processed=0`, `rejected=1`
  - terminal class `http_524`
  - endpoint `https://fast.vpsairobot.com/responses`

### Run B (gpt-5 tuned)

- profile: `/tmp/bl074_provider_profiles_gpt5.json`
- model: `gpt-5`
- env: `ARGUS_LLM_TIMEOUT_SECONDS=180`, `ARGUS_LLM_MAX_RETRIES=2`
- result artifact:
  - `runtime_archives/bl074/tmp/bl074_execute_replay_gpt5.json`
- outcome:
  - `processed=0`, `rejected=1`
  - terminal class `http_524`
  - endpoint `https://fast.vpsairobot.com/responses`

Runtime log snapshot (`runtime_archives/bl074/runtime/automation-runtime.attempt-1.gpt5.log`)
shows first attempt at `/v1/responses` then fallback `/responses`, both ending
at retryable gateway timeout class.

## Findings

1. Auth blocker remains cleared (no terminal `http_401` observed).  
2. Dominant blocker moved from local timeout exhaustion to upstream gateway
   timeout (`http_524`).  
3. Switching model (`gpt-5.4` -> `gpt-5`) did not remove the `http_524` class,
   indicating this is not a single-model-only regression.  
4. Runtime startup log still reports `timeout_recovery_retries=1` during these
   runs even when `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0` was exported at
   execute entrypoint; this indicates delegate env propagation for that knob is
   not currently wired.

## Outcome

`BL-20260325-074` is completed as timeout-stability validation phase:

- tuned replay attempts executed and archived
- blocker class is concretely identified as `http_524` under aligned profile
- next blocker is source/runtime-level mitigation for provider gateway timeout
  resilience and timeout-recovery knob propagation.

## Next Blocker

Queue `BL-20260325-075`:

- propagate timeout-recovery env control into delegated worker runtime
- add/validate stronger gateway-timeout resilience path for aligned provider
  profile so governed replay can reach automation success.
