# Transient Retry Policy Observation And Tuning Report

## Objective

Complete `BL-20260326-079` by observing repo-baseline transient retry behavior under repeated governed replays, then tuning policy/knobs when evidence shows insufficiency.

## Scope

In scope:

- repeated governed replay observation under repo baseline profile
- classify dominant transient failure classes from runtime evidence
- tune execute orchestration transient policy with focused tests
- rerun governed replay to verify post-tune behavior

Out of scope:

- provider-side SLA remediation
- broad scheduler redesign

## Baseline Observation (Pre-Tune)

Replay setup (baseline observation matrix):

- `ARGUS_PROVIDER_PROFILE=fast_chat_governed_baseline`
- `ARGUS_PROVIDER_PROFILES_FILE` unset
- `ARGUS_LLM_MAX_RETRIES=1`
- `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`
- `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- command:
  - `python3 skills/execute_approved_previews.py --once --preview-id preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153 --test-mode off --allow-replay`

Evidence summary (`runtime_archives/bl079/tmp/bl079_replay_matrix_budget1.tsv`):

- run01: rejected, class=`timeout`, `retries_used=0`
- run02: rejected, class=`timeout`, `retries_used=0`
- run03: rejected, class=`timeout`, `retries_used=0`

Conclusion:

- current transient policy (only `http_524`) did not cover observed dominant transient class (`timeout`) in this window.

## Tuning

### 1) Expand transient automation class coverage

Updated `skills/execute_approved_previews.py`:

- `TRANSIENT_AUTOMATION_ERROR_CLASSES` broadened from:
  - `{ "http_524" }`
- to:
  - `{ "http_524", "http_502", "timeout" }`

Rationale:

- replay evidence exposed real transient failures on `timeout` and `http_502` that should be recoverable by bounded in-process retry under the same governance contract.

### 2) Focused regression coverage

Updated `tests/test_execute_approved_previews.py`:

- `test_process_approval_retries_once_for_timeout_then_succeeds`
- `test_process_approval_retries_once_for_http_502_then_succeeds`

Validation:

- `python3 -m unittest -v tests/test_execute_approved_previews.py` passed (`9/9`)

## Post-Tune Governed Evidence

Tuned observation matrix (`runtime_archives/bl079/tmp/bl079_replay_matrix_budget1_tuned.tsv`):

- run01: rejected, class=`http_502`, `retries_used=0` (before `http_502` class landed)
- run02: rejected, class=`timeout`, `retries_used=1` (timeout transient retry path engaged)

Final replay after both class additions (`runtime_archives/bl079/tmp/bl079_replay_matrix_budget1_final.tsv`):

- run01: `processed=1`, `critic_verdict=pass`, `retries_used=0`

Archived artifacts:

- runtime/state/tmp evidence under `runtime_archives/bl079/`
- representative files:
  - `runtime_archives/bl079/tmp/bl079_replay_matrix_budget1.tsv`
  - `runtime_archives/bl079/tmp/bl079_replay_matrix_budget1_tuned.tsv`
  - `runtime_archives/bl079/tmp/bl079_replay_matrix_budget1_final.tsv`
  - `runtime_archives/bl079/runtime/automation-runtime.run01.budget1.final.log`
  - `runtime_archives/bl079/runtime/critic-output.run01.budget1.final.json`

## Outcome

`BL-20260326-079` objective is achieved:

- repeated governed observation was executed and archived
- insufficient baseline policy coverage was identified from evidence
- transient retry policy was tuned to cover observed classes (`timeout`, `http_502`, `http_524`)
- focused tests were added and passed
- post-tune governed replay reached `processed=1 / critic_verdict=pass`

## Residual Risk And Next Blocker

Residual risk remains provider-side variability (including sustained timeout/5xx bursts) beyond a bounded in-process retry budget.

Queue next blocker:

- `BL-20260326-080`: quantify pass-rate and latency tradeoff across retry budgets (`1` vs `2`) under short controlled replay windows, then freeze recommended default/profile guidance.
