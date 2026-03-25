# Automation Runtime Provider Availability/Failover Completion Report

## Objective

Close `BL-20260325-069` by proving governed runtime execution can reach critic
handoff without terminal provider availability failure.

## Context

Iteration-1 hardening completed runtime-side compatibility and responses
candidate routing, but governed replays against `https://aixj.vip` still ended
with terminal `http_502`.

## Completion Evidence

### 1) Backup provider health check

Using credentials/base URL from Desktop file `备用key.rtf`, endpoint probes for
responses API returned success:

- `https://fast.vpsairobot.com/v1/responses` -> `200`
- `https://fast.vpsairobot.com/responses` -> `200`

Models checked:

- `gpt-5.4`
- `gpt-5-codex`

### 2) Governed replay with backup provider passed end-to-end

Replay command (same approved preview):

- `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Result summary:

- `status = done`
- `processed = 1`
- `rejected = 0`
- `decision_reason = critic_verdict=pass`

Runtime handoff evidence:

- automation task `AUTO-20260325-874` completed `success`
- critic task `CRITIC-20260325-290` completed `success`
- final approval sidecar state is `processed` with `critic_verdict=pass`

Archived evidence:

- `runtime_archives/bl069/tmp/bl069_execute_replay_backup_provider.json`
- `runtime_archives/bl069/runtime/AUTO-20260325-874.backup_provider_pass.json`
- `runtime_archives/bl069/runtime/automation-runtime.backup_provider_pass.log`
- `runtime_archives/bl069/runtime/automation-output.backup_provider_pass.json`
- `runtime_archives/bl069/runtime/CRITIC-20260325-290.backup_provider_pass.json`
- `runtime_archives/bl069/runtime/critic-runtime.backup_provider_pass.log`
- `runtime_archives/bl069/runtime/critic-output.backup_provider_pass.json`
- `runtime_archives/bl069/state/preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153.backup_provider_pass.result.json`

## Outcome

`BL-20260325-069` done condition is satisfied:

- one governed real execute reached critic handoff and completed with pass
- no terminal provider availability failure blocked initial execution path

Residual note:

- `aixj.vip` path still showed `http_502` during earlier attempts; this report
  confirms runtime availability is recoverable with a healthy provider endpoint.
