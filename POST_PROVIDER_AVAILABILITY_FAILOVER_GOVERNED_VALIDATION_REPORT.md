# Post BL-069 Governed Validation Report

## Objective

Validate `BL-20260325-069` on one fresh governed candidate using the required
flow:

- smoke
- regeneration
- preview
- approval
- real execute

and confirm runtime reaches critic handoff without provider availability/failover
blockers.

## Scope

- origin: `trello:69c24cd3c1a2359ddd7a1bf8`
- regeneration token: `regen-20260325-bl070-001`
- provider endpoint for real execute: `https://fast.vpsairobot.com` (responses
  health probe already verified)

## Run Summary

### 1) Trello read-only smoke

- sandbox smoke output archived:
  - `runtime_archives/bl070/tmp/bl070_smoke_sandbox.json`
- elevated smoke output archived:
  - `runtime_archives/bl070/tmp/bl070_smoke_elevated.json`
- live mapped candidate captured:
  - `runtime_archives/bl070/tmp/bl070_live_mapped_preview.json`

Smoke result for target origin was `pass` with `read_count=1`.

### 2) Regeneration + ingest

- generated inbox payload:
  - `inbox/trello-69c24cd3c1a2359ddd7a1bf8-regen-20260325-bl070-001.json`
- ingest command result archive:
  - `runtime_archives/bl070/tmp/bl070_ingest_once.json`

Ingest decision:

- `status = processed`
- `decision = preview_created_pending_approval`
- `preview_id = preview-trello-69c24cd3c1a2359ddd7a1bf8-cb445a22289d`

### 3) Approval

- approval file:
  - `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-cb445a22289d.json`
- pre-execute preview state:
  - `approved = false`
  - `execution.status = pending_approval`
  - `execution.executed = false`
  - `execution.attempts = 0`

### 4) Real execute

First non-elevated execute (expected sandbox constraint evidence):

- archive:
  - `runtime_archives/bl070/tmp/bl070_execute_once_sandbox.json`
- result:
  - `status = rejected`
  - reason: Docker client initialization unavailable in sandbox context

Elevated replay execute:

- archive:
  - `runtime_archives/bl070/tmp/bl070_execute_once_elevated.json`
- result:
  - `status = done`
  - `processed = 1`
  - `rejected = 0`
  - `decision_reason = critic_verdict=pass`

Task evidence:

- automation task:
  - `AUTO-20260325-875`
  - runtime/output archives under `runtime_archives/bl070/runtime/`
- critic task:
  - `CRITIC-20260325-291`
  - runtime/output archives under `runtime_archives/bl070/runtime/`

Final preview execution state:

- `approved = true`
- `execution.status = processed`
- `execution.executed = true`
- `decision_reason = critic_verdict=pass`

## Conclusion

`BL-20260325-070` validation objective is satisfied:

- one fresh governed candidate completed full flow from smoke to real execute
- automation reached critic handoff
- critic verdict is `pass`
- no provider availability/failover blocker prevented the governed execute in
  elevated real-run conditions

## Archive

All phase evidence is preserved under:

- `runtime_archives/bl070/tmp/`
- `runtime_archives/bl070/runtime/`
- `runtime_archives/bl070/state/`
