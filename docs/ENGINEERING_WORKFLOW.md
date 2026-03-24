# Engineering Workflow

## Purpose

This document turns the repo's current working norms into a standard software
delivery flow. The goal is not to redesign the system. The goal is to prevent
future work from depending on personal memory, local shell state, or undocumented
exceptions.

## Core Principles

1. One source of truth per concern.
2. One explicit gate per state transition.
3. Fail closed when remote, branch, credential, or sample state is ambiguous.
4. Treat runtime audit residue as governed state, not casual dirty diff.
5. Prefer incremental hardening over architecture churn.

## Document Responsibilities

Use documents by role, not by recency guesswork.

### Constitutional constraints

- `BASELINE_FREEZE_NOTE.md`
- `RUNTIME_CONTRACT.md`

These files define the rules that should not drift silently.

### Current-state ledger

- `PROJECT_CHAT_AND_WORK_LOG.md`

This is the default answer to: "What is the repo's current real state?"

Rules:

- Update it when a phase materially changes current behavior or blockers.
- Track it in git before phase closeout.
- Do not let a local-only copy become the team's only state record.

### Capability evidence

- phase reports in repo root
- `PROCESSED_FINALIZATION_REPORT.md`

These files prove what has already been implemented and how it was validated.

### Historical snapshots

- `MAINLINE_GAP_AUDIT.md`

This file is still useful, but only as the `Phase 8F` gap snapshot. Do not treat
it as the live status source after later implementation evidence exists.

## Remote And Branch Policy

### Required remote posture

- `origin` is the single authoritative code remote.
- Formal smoke or finalization runs are not allowed if `git remote -v` is empty.
- Formal finalization runs must use explicit `GIT_PUSH_REMOTE` and
  `GIT_PUSH_BRANCH`. No implicit branch guessing.

### Branch responsibilities

- `main`
  - reviewed code only
  - no direct push from humans
  - no direct push from automation helpers
- Human development branches
  - `feat/*`
  - `fix/*`
  - `phase8*/...`
- Automation / finalization branches
  - `automation/processed`
  - `ops/finalization/*`

### Merge policy

- Code changes return to `main` via PR.
- Automation-generated runtime output must not be mixed into ordinary feature PRs.
- If automation output must return to `main`, do it through a dedicated PR with
  explicit review and evidence.

## Mandatory Gates

### Gate A: Pre-run

Run `docs/PRE_RUN_CHECKLIST.md` before any real:

- Trello read integration
- Trello writeback / Done
- Git push finalization
- formal upstream smoke

### Gate B: Pre-merge / pre-ship

Run `docs/PRE_MERGE_CHECKLIST.md` before:

- merge to protected branch
- phase freeze
- ship / formal closeout

### Gate C: Phase exit

Every phase closes only when all three are true:

1. The exit condition is explicit.
2. The evidence doc is written or updated.
3. The current-state ledger is updated.

## Standard Phase Flow

1. Define phase scope.
   - objective
   - non-goals
   - exit condition
   - smoke and regression plan
2. Create the correct branch.
   - human work on topic branch
   - no direct development on `main`
3. Implement with the constitutional rules preserved.
   - do not broaden scope mid-phase without updating the plan
4. Run local verification.
   - ordinary phase: `1 smoke + 3 regression`
   - key milestone: `5 formal validation rounds`
5. Run pre-run gate if the phase touches real Git / Trello integration.
6. Open PR with evidence, risk note, rollback note, and document updates.
7. Run one formal smoke for the exact stage being closed.
8. Freeze the phase.
   - update current-state ledger
   - update capability evidence
   - mark stale snapshots as historical if needed
   - resolve runtime audit residue

## Runtime Audit Residue Policy

Files under `preview/`, `approvals/`, and `processed/` can contain real runtime
truth. They are not ordinary source edits.

Before merge, ship, or formal smoke, every residue must be classified as one of:

1. Intentional tracked audit evidence.
2. Runtime state that should be archived or copied into a report / sidecar.
3. A local-only experimental artifact that must stay off the merge target branch.

Rules:

- Do not blindly `git reset` runtime residue.
- Do not merge a branch with unclassified runtime residue.
- Register classified residue in `docs/RUNTIME_RESIDUE_REGISTRY.tsv`.
- If a residue is kept, reference it from the relevant report.
- If a residue should not remain tracked, move the truth into the appropriate
  sidecar or evidence doc, then return the working tree to a governed state.

## Minimum Test Baseline

The current repo-level minimum command set is:

```bash
python3 -m unittest -v tests/test_argus_hardening.py
python3 -m unittest -v tests/test_processed_finalization.py
scripts/premerge_check.sh
```

For finalization work, also run:

```bash
scripts/preflight_finalization_check.sh <preview_json_path>
```

## CI Baseline

The repository should keep a minimal CI job that runs:

- `python3 -m unittest -v tests/test_argus_hardening.py`
- `python3 -m unittest -v tests/test_processed_finalization.py`
- shell syntax checks for governance scripts under `scripts/`

CI is a baseline guard, not a substitute for the local pre-run and pre-merge gates.

## Definition Of Done For A Real Integration Step

An integration step is not done just because code exists. It is done only when:

1. The branch and remote target are explicit.
2. Required credentials are present.
3. Smoke validation passed in the intended environment.
4. Replay / retry semantics are still truthful.
5. Current-state and evidence docs are both updated.
