# Phase 7.2 Stability Regression Report

## Scope
- Repo: `~/openclaw-team`
- Input set: `~/Desktop/pdf样本` (same 5 PDFs)
- Objective: verify stability and state credibility, not output quality optimization
- Execution date: 2026-03-19

## Regression Plan
1. Re-run same sample batch for 5 consecutive rounds.
2. Each round executes:
   - dry-run (`--dry-run`)
   - real output run
3. Add 2 controlled-failure scenarios to verify honest failure behavior.
4. Check consistency dimensions:
   - `success/failed` stability
   - Excel generation stability
   - state credibility (`rc` vs `status`)
   - runtime/task/workspace side effects
   - residual containers / abnormal execution state
   - cross-run contamination or overwrite

## Baseline Snapshot (Before Rounds)
- Running containers baseline (11):
  - `manager`
  - `openclaw-sidecar_dionysus-1`
  - `openclaw-sidecar_midas-1`
  - `openclaw-sidecar_argus-1`
  - `openclaw-sidecar_artemis-1`
  - `agent_hermes`
  - `agent_artemis`
  - `agent_argus`
  - `agent_midas`
  - `agent_athena`
  - `searxng_local`
- `tasks` file count baseline: `26`
- `workspaces` file count baseline: `74`
- `runtime.log` file count baseline: `15`

## Round Results (5 rounds)
| Round | Dry-run status | Dry success/failed | Real status | Real success/failed | Excel generated | Container unchanged | Task/Workspace counts unchanged |
|---|---|---|---|---|---|---|---|
| 1 | success | 5/0 | success | 5/0 | yes | yes | yes |
| 2 | success | 5/0 | success | 5/0 | yes | yes | yes |
| 3 | success | 5/0 | success | 5/0 | yes | yes | yes |
| 4 | success | 5/0 | success | 5/0 | yes | yes | yes |
| 5 | success | 5/0 | success | 5/0 | yes | yes | yes |

Real output files:
- `/tmp/phase7_2/round_01_real.xlsx`
- `/tmp/phase7_2/round_02_real.xlsx`
- `/tmp/phase7_2/round_03_real.xlsx`
- `/tmp/phase7_2/round_04_real.xlsx`
- `/tmp/phase7_2/round_05_real.xlsx`

All 5 real outputs were generated successfully and had consistent size (`7035` bytes).

## Controlled Failure Regression
### Scenario A: invalid output path
Command shape:
- `--output-xlsx /dev/null/phase7_fail.xlsx`

Observed:
- return code: `3`
- status: `failed`
- error: `[Errno 17] File exists: '/dev/null'`
- verdict: expected failure, passed

### Scenario B: invalid input directory
Command shape:
- `--input-dir ~/Desktop/pdf样本_NOT_EXIST`

Observed:
- return code: `2`
- status: `failed`
- error: `Input directory does not exist: ...`
- verdict: expected failure, passed

## Credibility and Isolation Checks
- `status` vs return code consistency:
  - all successful rounds: `rc=0`, `status=success`
  - controlled failure rounds: non-zero rc with `status=failed`
- runtime/task/workspace side effects:
  - no drift in `tasks/workspaces/runtime.log` file counts
  - no new unexpected runtime state artifacts detected
- residual container check:
  - container set unchanged across rounds
  - no extra or zombie container from this regression
- task cross-read/overwrite:
  - pilot runs used isolated output paths per round
  - no evidence of cross-run contamination

## Randomness / Flakiness
- No random instability observed in 5 consecutive rounds.
- Success/failure counts and output generation were deterministic in this run set.

## Final Conclusion
- **stable**

## Raw Result Artifact
- `/tmp/phase7_2/phase7_2_regression_results.json`
