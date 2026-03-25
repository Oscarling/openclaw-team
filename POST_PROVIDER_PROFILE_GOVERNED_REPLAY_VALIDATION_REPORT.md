# Post Provider-Profile Governed Replay Validation Report

## Objective

Validate `BL-20260325-071` on one governed replay by running execute with
profile-selected provider configuration, without manual desktop-secret extraction
in the execution step.

## Scope

In scope:

- one governed replay execute (`--test-mode off --allow-replay`)
- runtime profile selection via:
  - `ARGUS_PROVIDER_PROFILE`
  - `ARGUS_PROVIDER_PROFILES_FILE`
- evidence archival under `runtime_archives/bl072/`

Out of scope:

- rotating provider credentials
- changing runtime retry policy
- fresh smoke/regeneration cycle

## Runtime Setup Used

- sourced baseline env from `/tmp/trello_env.sh` (ambient base remained
  `https://aixj.vip/v1`)
- provided profile file at `/tmp/bl072_provider_profiles.json` with profile
  `bl072_fast_override`:
  - `api_base=https://fast.vpsairobot.com/v1`
  - `wire_api=responses`
  - `api_key_env=OPENAI_API_KEY`
  - fallback response URL `https://fast.vpsairobot.com/responses`

No desktop file parsing was performed in this execute step.

## Probe Snapshot (Pre-Run)

Saved at `runtime_archives/bl072/tmp/bl072_probe_matrix.txt`:

- `https://aixj.vip/v1/responses` -> `502`
- `https://aixj.vip/responses` -> `502`
- `https://fast.vpsairobot.com/v1/responses` -> `401`
- `https://fast.vpsairobot.com/responses` -> `401`

## Governed Replay Execution

Command class:

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Primary result (`runtime_archives/bl072/tmp/bl072_execute_replay_profile.json`):

- `status=done`
- `processed=0`
- `rejected=1`
- rejection reason includes terminal:
  - `class=http_401`
  - `endpoint=https://fast.vpsairobot.com/responses`

Runtime evidence (`runtime_archives/bl072/runtime/automation-runtime.attempt-1.profile.log`)
shows profile override was active:

- worker started on
  `https://fast.vpsairobot.com/v1/responses (wire_api=responses)`
- then auth-fallback retried to
  `https://fast.vpsairobot.com/responses`
- terminal class remained `http_401`

## Outcome

`BL-20260325-072` validation objective is satisfied:

- governed replay executed with profile-selected provider config
- profile path overrode ambient base (`aixj.vip`) to profile base (`fast.vpsairobot.com`)
- evidence is archived and traceable

But live execution is still blocked by provider authentication (`http_401`) for
this key/profile pairing.

## Next Blocker

Queue next blocker item:

- align provider profile/credential set so profile-selected execute can reach
  automation success and critic handoff under real run conditions.
