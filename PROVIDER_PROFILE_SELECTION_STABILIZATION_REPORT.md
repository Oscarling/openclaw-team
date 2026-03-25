# Provider Profile Selection Stabilization Report (BL-20260325-071)

## Objective

Close `BL-20260325-071` by eliminating the BL-070 manual desktop-secret dependency.
The governed execute path must select an approved provider profile from repo/runtime
configuration, without ad-hoc key/base extraction during each run.

## Scope

In scope:

- profile-based provider selection in delegate runtime env assembly
- fail-closed handling for invalid profile or missing key references
- backward compatibility when no profile is selected
- focused regression coverage
- configuration template for profile definitions

Out of scope:

- rotating or issuing provider keys
- changing worker runtime HTTP/retry semantics
- re-running a full governed execute flow in this backlog item

## Changes

### 1) Added provider profile selection to `build_worker_env(...)`

Updated `skills/delegate_task.py`:

- added profile resolution path:
  - `ARGUS_PROVIDER_PROFILE`
  - `ARGUS_PROVIDER_PROFILES_FILE` (default: `contracts/provider_profiles.json`)
- added profile loader and normalizers:
  - object or `{ "profiles": { ... } }` payload support
  - string/list fallback fields normalized to runtime env CSV format
- added API key resolution policy per profile:
  - `api_key` / `openai_api_key`
  - `api_key_env`
  - `api_key_secret`
- profile-selected values now override ambient defaults when explicitly enabled

### 2) Added fail-closed guarantees for profile/key misconfiguration

`build_worker_env(...)` now raises runtime errors when:

- selected profile file is missing or invalid JSON
- selected profile name does not exist
- profile references an unset `api_key_env`
- profile references an unavailable `api_key_secret`

This prevents silent fallback to unintended provider credentials.

### 3) Added profile configuration template and contract docs

- added `contracts/provider_profiles.example.json` for non-secret profile structure
- extended `RUNTIME_CONTRACT.md` with BL-071 provider profile contract section

## Regression Tests

Updated `tests/test_argus_hardening.py` with:

- `test_build_worker_env_uses_selected_provider_profile`
- `test_build_worker_env_profile_key_env_missing_raises`
- `test_build_worker_env_without_profile_keeps_legacy_env_resolution`

Validation:

- `python3 -m unittest -v tests/test_argus_hardening.py` passed (`21/21`)

## Usage Notes

Example runtime selection:

```bash
export ARGUS_PROVIDER_PROFILE=aixj_vip_backup
export ARGUS_PROVIDER_PROFILES_FILE=contracts/provider_profiles.json
export OPENAI_API_KEY_AIXJ_VIP='***'
python3 skills/execute_approved_previews.py --once --test-mode off
```

Without `ARGUS_PROVIDER_PROFILE`, runtime behavior remains backward-compatible
with existing `OPENAI_*` and secret-based resolution.

## Outcome

`BL-20260325-071` done condition is satisfied at source level:

- governed execute provider selection can now be driven by repository/runtime
  profile configuration
- manual desktop secret extraction is no longer required by design
- misconfiguration is fail-closed and test-covered
