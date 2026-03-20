# Critic Path Diagnosis and Convergence Report

## Scope and Boundaries
- Scope: diagnose and converge the unstable Critic path in full-chain validation.
- Explicit non-scope (kept unchanged): `skills/delegate_task.py`, `dispatcher/worker_runtime.py`, one-shot model, contract source-of-truth, preview/approval gate.
- No automatic iteration loop was introduced.

## Evidence Reviewed
- `FULL_CHAIN_OPERATIONAL_VALIDATION_REPORT.md`
- `/tmp/fullchain_5round_summary.json`
- Historical unstable rounds:
  - `tasks/CRITIC-20260320-173.json`
  - `workspaces/critic/CRITIC-20260320-173/output.json`
  - `workspaces/critic/CRITIC-20260320-173/runtime.log`
  - `tasks/CRITIC-20260320-445.json`
  - `workspaces/critic/CRITIC-20260320-445/output.json`
  - `workspaces/critic/CRITIC-20260320-445/runtime.log`
- Corresponding automation evidence:
  - `tasks/AUTO-20260320-563.json`
  - `tasks/AUTO-20260320-107.json`
- Post-fix 3-round smoke evidence:
  - `/tmp/critic_path_3round_summary.json`
  - `tasks/CRITIC-20260320-611.json`
  - `tasks/CRITIC-20260320-953.json`
  - `tasks/CRITIC-20260320-200.json`

## Root Cause Diagnosis

### Round 1 failed: `CRITIC-20260320-173`
- Observed failure:
  - `workspaces/critic/CRITIC-20260320-173/output.json` shows:
    - `status: failed`
    - `errors: ["success/partial output requires at least one artifact"]`
    - `artifacts: []`
- Root cause category:
  - **Output contract stability + prompt/task shaping gap**
- Why:
  - Critic output did not guarantee required review artifact emission when returning non-failed semantic content.
  - Manager-side shaping did not enforce “always emit review artifact” strongly enough.

### Round 5 partial: `CRITIC-20260320-445`
- Observed partial:
  - `workspaces/critic/CRITIC-20260320-445/output.json` shows:
    - `status: partial`
    - error about inaccessible script content
    - review artifact exists
    - verdict equivalent to `needs_revision`
- Root cause category:
  - **Input organization gap (insufficient reviewable evidence in Critic input)**
- Why:
  - Critic received artifact path references, but not deterministic content snapshots; in some executions it reported artifact visibility/context limitations.

### Why `needs_revision` clustered
- Main cluster was not control-chain instability.
- Concentration came from:
  - **input organization**: insufficient stable evidence for grounded review in some runs.
  - **task shaping**: verdict and review artifact requirements were not explicit enough.
  - **verdict normalization**: metadata key variants (`review_verdict` vs `verdict`) needed unified extraction.
- Not a core gate issue:
  - preview -> approval -> execute chain remained intact.

## Minimal Convergence Fixes Applied

### 1) `skills/execute_approved_previews.py`
- Enhanced `extract_critic_verdict`:
  - supports `metadata.verdict` and `metadata.review_verdict`.
- Added `_read_artifact_text`:
  - reads `artifacts/...` content safely (path guard + truncation).
- Added `_critic_review_contract`:
  - explicit contract requiring verdict + review artifact even under partial evidence.
- Updated `build_critic_from_automation`:
  - injects normalized artifacts and `artifact_snapshots`.
  - injects `review_contract` and `review_template`.
  - tightens Critic constraints for deterministic artifact/verdict behavior.
- Problem addressed:
  - prevents no-artifact outcomes and reduces evidence-visibility instability.

### 2) `adapters/local_inbox_adapter.py`
- Strengthened Critic objective/constraints:
  - requires explicit verdict in metadata.
  - requires review markdown artifact generation.
- Problem addressed:
  - stabilizes manager-to-critic task intent and output shape.

## 3-round Smoke Re-run (post-fix)
- Execution chain per round:
  - `inbox -> ingest -> preview(pending_approval) -> approval -> execute_approved_previews -> Automation -> Critic`
- Credential mode:
  - command-level `OPENAI_*` injection (same as validated baseline)

| Round | Automation status | Critic status | Critic verdict | Review artifact | Final decision | Replay protection |
|---|---|---|---|---|---|---|
| 1 | success | success | pass | present | processed | pass (skipped on replay) |
| 2 | success | success | needs_revision | present | rejected | pass (skipped on replay) |
| 3 | success | success | pass | present | processed | pass (skipped on replay) |

Additional integrity checks:
- Critic `failed` in 3 rounds: `0`
- Critic no-artifact in 3 rounds: `0`
- Mis-execution: `no`
- Duplicate execution on replay: `no`
- Residual abnormal (`inbox` / `processing` pending): none

## Convergence Assessment
- Convergence target for this task was met:
  - no unexplained Critic failures
  - no missing review artifact
  - partial/needs_revision behavior is now explainable and contract-consistent.
- `needs_revision` may still appear when review content flags substantive quality issues; this is expected gate behavior, not path instability.

## Recommendation
- Recommend re-entering 5-round formal validation: **Yes**.
- Rationale:
  - path-level instability has been converged in 3-round smoke;
  - replay protection and approval gate remain correct.
- Remaining non-blocking observation:
  - quality verdict variance (`pass` vs `needs_revision`) reflects artifact content quality, not control-chain reliability.
