# Post Provider Credential/Profile Alignment Report

## Objective

Address `BL-20260325-073` by restoring provider credential/profile alignment
for profile-selected execute, so terminal auth failures (`http_401`) are removed
from the governed replay path.

## Scope

In scope:

- align runtime credential source with backup provider profile
- run one governed replay execute with profile-selected config
- verify whether dominant blocker remains auth or shifts to another class
- archive runtime evidence

Out of scope:

- full provider timeout/SLA stabilization
- model prompt/runtime behavior changes

## Runtime Alignment Applied

Credential source:

- backup key was loaded from `~/Desktop/备用key.rtf` at run time
- no secret value was committed into repository files

Profile selection:

- `ARGUS_PROVIDER_PROFILE=bl073_fast_backup`
- `ARGUS_PROVIDER_PROFILES_FILE=/tmp/bl073_provider_profiles.json`
- profile base: `https://fast.vpsairobot.com/v1`
- wire API: `responses`
- key source: `api_key_env=OPENAI_API_KEY_BACKUP`

## Probe Evidence

Saved at `runtime_archives/bl073/tmp/bl073_probe_matrix.txt`:

- `https://fast.vpsairobot.com/v1/responses` with models `gpt-5.4`,
  `gpt-5-codex`, `gpt-5` => all `200`
- `https://fast.vpsairobot.com/responses` with models `gpt-5.4`,
  `gpt-5-codex`, `gpt-5` => all `200`

This confirms credential/profile pairing is accepted by provider endpoint.

## Governed Replay Result

Executed:

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Result (`runtime_archives/bl073/tmp/bl073_execute_replay_profile.json`):

- `status=done`
- `processed=0`
- `rejected=1`
- terminal class shifted to timeout:
  - `class=timeout`
  - `endpoint=https://fast.vpsairobot.com/responses`
  - `attempts=4/4`

Runtime log (`runtime_archives/bl073/runtime/automation-runtime.attempt-1.profile.log`) shows:

- worker started at profile endpoint with `wire_api=responses`
- no `http_401` terminal failure
- retries exhausted on timeout (including timeout recovery retry)

## Outcome

`BL-20260325-073` is complete as a credential/profile-alignment phase:

- terminal auth blocker (`http_401`) has been removed
- dominant blocker moved to provider timeout/stability under real replay

## Next Blocker

Queue next blocker:

- timeout/stability hardening for aligned provider profile so governed replay can
  reach automation success and critic handoff.
