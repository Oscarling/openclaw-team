# Persistent HTTP 524 Path Mitigation Report

## Objective

Close `BL-20260326-076` by mitigating persistent upstream `http_524` observed in
BL-075 and validating a governed execute path that reaches automation success.

## Scope

In scope:

- endpoint/wire-api probe matrix under aligned provider credentials
- one governed replay experiment on an alternate wire path
- evidence archival and backlog/worklog updates

Out of scope:

- provider infrastructure changes
- large runtime refactors beyond BL-075 hardening baseline

## Baseline from BL-075

- BL-075 had already fixed timeout-recovery propagation and enabled `http_524`
  timeout-recovery extension, but replay still ended with terminal
  `attempts=4/4, class=http_524` on responses endpoint.

## Probe Matrix

Evidence file:

- `runtime_archives/bl076/tmp/bl076_probe_matrix.txt`

Result summary:

- `https://fast.vpsairobot.com/v1/responses` -> `200`
- `https://fast.vpsairobot.com/responses` -> `200`
- `https://fast.vpsairobot.com/v1/chat/completions` -> `200`
- models tested: `gpt-5.4`, `gpt-5`, `gpt-5-codex`

This confirmed the provider was reachable on both wire families for lightweight
requests, so BL-076 proceeded with a governed replay on a chat-completions
stable path experiment.

## Governed Replay Experiment A

Experiment profile:

- file: `runtime_archives/bl076/tmp/bl076_provider_profiles.experiment_a.json`
- profile: `bl076_fast_chat`
- `api_base=https://fast.vpsairobot.com/v1`
- `wire_api=chat_completions`
- `model_name=gpt-5-codex`

Runtime knobs:

- `ARGUS_LLM_TIMEOUT_SECONDS=240`
- `ARGUS_LLM_MAX_RETRIES=2`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=2`

Replay command:

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

## Results

Primary replay result:

- `runtime_archives/bl076/tmp/bl076_execute_replay_experiment_a.json`
- outcome: `processed=1`, `rejected=0`, `critic_verdict=pass`

Sidecar result:

- `runtime_archives/bl076/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.result.json`
- outcome: `status=processed`, `decision_reason=critic_verdict=pass`

Worker evidence:

- automation success:
  - `runtime_archives/bl076/runtime/automation-output.experiment-a.json`
  - `runtime_archives/bl076/runtime/automation-runtime.experiment-a.log`
- critic success:
  - `runtime_archives/bl076/runtime/critic-output.experiment-a.json`
  - `runtime_archives/bl076/runtime/critic-runtime.experiment-a.log`

## Outcome

`BL-20260326-076` is complete.

- Persistent `http_524` blocker is mitigated in governed runtime path by
  validating an alternate stable wire path (`chat_completions`) under aligned
  provider profile.
- Governed replay reached full handoff with final `critic_verdict=pass`.

## Next Step

Queue `BL-20260326-077` to productize this validated path into a repository-
managed, repeatable provider-profile baseline (reduce ad-hoc temporary profile
setup for future governed runs).
