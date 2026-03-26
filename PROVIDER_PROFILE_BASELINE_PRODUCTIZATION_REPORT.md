# Provider Profile Baseline Productization Report

## Objective

Complete `BL-20260326-077` by converting the BL-076 validated chat path into a
repository-managed provider profile baseline and validating governed execute
without ad-hoc temporary profile files.

## Scope

In scope:

- repository-managed provider profile baseline file
- contract/documentation updates for baseline usage
- focused test coverage for default profile-file resolution path
- governed replay validation using only repo baseline profile selection

Out of scope:

- upstream provider SLA fixes
- broader multi-provider failover redesign

## Source/Productization Changes

### 1) Repository-managed baseline profile

- added: `contracts/provider_profiles.json`
- new baseline profile: `fast_chat_governed_baseline`
  - `api_base=https://fast.vpsairobot.com/v1`
  - `wire_api=chat_completions`
  - `model_name=gpt-5-codex`
  - `api_key_env=OPENAI_API_KEY_FAST`

### 2) Example profile alignment

- updated: `contracts/provider_profiles.example.json`
- includes `fast_chat_governed_baseline` so docs/template and repo baseline are
  consistent.

### 3) Contract documentation

- updated: `RUNTIME_CONTRACT.md`
- added BL-077 baseline section with minimal runtime setup:
  - export `OPENAI_API_KEY_FAST`
  - export `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
  - no temporary profile file required

### 4) Focused test

- updated: `tests/test_argus_hardening.py`
- added:
  `test_build_worker_env_uses_default_repo_profiles_file_when_not_overridden`
- validates that profile selection works via default
  `contracts/provider_profiles.json` when `ARGUS_PROVIDER_PROFILES_FILE` is
  unset.

## Governed Validation (Repo Baseline Only)

Validation constraints:

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset
- no `/tmp` temporary provider profile file used for execution

Replay command (elevated):

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

### Attempt A

- artifact: `runtime_archives/bl077/tmp/bl077_execute_replay_repo_profile.json`
- outcome: `processed=0`, `rejected=1`
- terminal class: `http_524` at
  `https://fast.vpsairobot.com/v1/chat/completions`

### Attempt B (same config, controlled rerun)

- artifact:
  `runtime_archives/bl077/tmp/bl077_execute_replay_repo_profile_attempt_b.json`
- outcome: `processed=1`, `rejected=0`, `critic_verdict=pass`
- runtime evidence confirms repo baseline profile path:
  - `runtime_archives/bl077/runtime/automation-runtime.repo-profile-pass.log`
  - startup line shows endpoint
    `https://fast.vpsairobot.com/v1/chat/completions`
    with `wire_api=chat_completions`

## Outcome

`BL-20260326-077` is complete:

- provider profile baseline is now repository-managed and documented
- governed execute can run successfully via repo baseline profile path without
  temporary profile files

Observed risk:

- intermittent upstream `http_524` persists (attempt A failed, attempt B
  passed), so reliability hardening remains as the next blocker.

## Next Blocker

Queue `BL-20260326-078`:

- characterize and improve single-pass reliability under the repo baseline
  profile path to reduce immediate manual rerun dependence.
