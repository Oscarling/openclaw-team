# Budget-2 Escalation Runbook Productization Report

## Objective

Complete `BL-20260326-082` by productizing a governed escalation runbook for
temporary `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=2` usage, including clear
activation/rollback criteria and at least one archived drill run.

## Scope

In scope:

- define explicit trigger, execution, rollback, and evidence rules
- record the rules in repository runtime contract
- run one governed `budget=2` drill and archive execute/runtime/state evidence

Out of scope:

- changing default retry budget from `1` to `2`
- provider-side SLA remediation

## Runbook Productization

Runbook contract is now documented in:

- `RUNTIME_CONTRACT.md` (section: BL-082 预算 `2` 临时升级触发与回滚 Runbook)

Covered controls:

- activation criteria (all required)
- fixed provider/runtime controls during drill
- mandatory rollback conditions
- minimum evidence bundle for auditability

## Drill Execution

Drill profile:

- preview: `preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153`
- temporary override: `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=2`
- fixed controls:
  - `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
  - `ARGUS_PROVIDER_PROFILES_FILE` unset
  - `ARGUS_LLM_MAX_RETRIES=1`
  - `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`

Drill summary (`runtime_archives/bl082/tmp/bl082_drill_summary.tsv`):

- `status=done`
- `processed=0`, `rejected=1`
- `critic_verdict=needs_revision`
- `automation_transient_retries_used=1`
- `wall_seconds=179`
- terminal reason included `LLM output not valid JSON`

## Evidence

Primary summary:

- `runtime_archives/bl082/tmp/bl082_drill_summary.tsv`

Execute artifacts:

- `runtime_archives/bl082/tmp/bl082_execute_replay_drill-b2.json`
- `runtime_archives/bl082/tmp/bl082_execute_replay_drill-b2.stderr.log`

Runtime/state archive:

- `runtime_archives/bl082/runtime/*drill-b2*`
- `runtime_archives/bl082/state/*drill-b2*`

## Decision

Default guidance remains unchanged:

- keep baseline default `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- allow `=2` only as governed temporary override via BL-082 runbook

Rollback confirmation:

- temporary override is scope-limited to the drill command and not persisted as
  baseline environment default.

## Outcome

`BL-20260326-082` objective is achieved:

- runbook trigger/rollback policy is productized in repo contract
- governed drill evidence is archived and traceable
- baseline default is preserved without drift
