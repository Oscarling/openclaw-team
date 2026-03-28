# Project Backlog

## Purpose

`PROJECT_BACKLOG.md` is the single source of truth for open project work. If a
mainline task, sideline, blocker, debt item, or future idea is worth remembering
beyond the current shell session, it must be recorded here before review, ship,
or merge.

`PROJECT_CHAT_AND_WORK_LOG.md` remains the current-state ledger. This file answers
a different question: "What still needs attention, under what conditions, and in
what order?"

GitHub issues are a mirror for worthwhile backlog items, not the authority. Until
sync automation exists, `PROJECT_BACKLOG.md` wins if an issue and the backlog
disagree.

Use `-` when a field is intentionally empty. The `###` heading is the item's
canonical `id`.

## Required Fields

Every backlog item must include these exact fields:

- `title`
- `type`
- `status`
- `phase`
- `priority`
- `owner`
- `depends_on`
- `start_when`
- `done_when`
- `source`
- `link`
- `issue`
- `evidence`
- `last_reviewed_at`
- `opened_at`

Allowed enum values:

- `type`: `mainline`, `sideline`, `blocker`, `debt`, `future`
- `status`: `planned`, `active`, `parked`, `blocked`, `done`
- `phase`: `now`, `next`, `later`
- `priority`: `p0`, `p1`, `p2`, `p3`

## Review Rules

- Run a backlog sweep before review, ship, or merge.
- If new work appears during implementation, add it here before asking for review.
- Update `status`, `phase`, and `last_reviewed_at` whenever the item's real state
  changes.
- When an item becomes `done`, replace `evidence: -` with concrete proof.
- For `phase=now` items with `status=planned|active|blocked`, create a mirrored
  GitHub issue and record it in `issue`.
- `deferred:...` is acceptable only for non-`now` items.

## Backlog Items

### BL-20260324-001
- title: Install the project backlog anti-slip governance kit
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: Governance baseline branch is available for follow-up process hardening
- done_when: PROJECT_BACKLOG.md, backlog lint, CI, and merge gates are all merged through normal review
- source: PROJECT_CHAT_AND_WORK_LOG.md
- link: https://github.com/Oscarling/openclaw-team/pull/1
- issue: https://github.com/Oscarling/openclaw-team/issues/3
- evidence: PR #1 merged to `main` on 2026-03-24 as merge commit `9b1ed4c`, landing PROJECT_BACKLOG.md, backlog lint, CI, and merge-readiness gates
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-002
- title: Merge formal preview smoke hardening through a reviewed PR
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: fix/formal-preview-smoke-hardening branch is ready for review
- done_when: The hardening PR merges to main with required checks green
- source: PROCESSED_FINALIZATION_REPORT.md
- link: https://github.com/Oscarling/openclaw-team/pull/2
- issue: https://github.com/Oscarling/openclaw-team/issues/4
- evidence: PR #2 merged to `main` on 2026-03-24 as merge commit `5c7a31b`, after the shared CI dependency fix turned `baseline-tests` green
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-003
- title: Enable branch protection for the primary branch with required CI and PR gating
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-001, BL-20260324-002, BL-20260324-006
- start_when: Governance and smoke-hardening PR branches are ready to enter normal merge flow and GitHub plan/public-visibility limits no longer block branch protection
- done_when: The primary branch rejects direct push and requires pull-request based changes, up-to-date CI, and conversation resolution under the chosen single-maintainer policy
- source: PROJECT_CHAT_AND_WORK_LOG.md
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: https://github.com/Oscarling/openclaw-team/issues/5
- evidence: Branch protection is enabled on `main` with strict required checks `baseline-tests` and `shell-checks`, stale review dismissal, required conversation resolution, `required_approving_review_count=0`, `enforce_admins=true`, and force-push/deletion blocked under the final single-maintainer policy
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-004
- title: Mirror active backlog items into GitHub issues
- type: sideline
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-001
- start_when: The backlog format and lint gate are merged so issue mirroring has a stable source
- done_when: Each phase=now actionable backlog item has a linked GitHub issue and mirror checks run in local gates plus CI
- source: PROJECT_BACKLOG.md
- link: https://github.com/Oscarling/openclaw-team/pull/7
- issue: https://github.com/Oscarling/openclaw-team/issues/6
- evidence: PR #7 merged to `main` on 2026-03-24 as merge commit `67b4246`, landing `scripts/backlog_sync.py`, the issue template, and CI/premerge issue-mirror enforcement
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-005
- title: Pin TRELLO_DONE_LIST_ID in the formal runtime environment
- type: debt
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-002
- start_when: The formal preview smoke hardening is merged and the runtime environment is ready for one config pass
- done_when: Formal finalization no longer depends on list-name lookup for the Done list
- source: PROCESSED_FINALIZATION_REPORT.md
- link: /tmp/trello_env.sh
- issue: https://github.com/Oscarling/openclaw-team/issues/12
- evidence: `scripts/pin_trello_done_list.py` was added, `/tmp/trello_env.sh` now exports `TRELLO_DONE_LIST_ID`, and `/private/tmp/trello_env.sh.bak-20260324T064207Z` preserves the prior runtime env file
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-006
- title: Resolve GitHub plan limitation blocking private-repo branch protection
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: Main branch policy must move from convention to enforced platform settings
- done_when: The repo either supports GitHub branch protection or rulesets on the current plan, becomes public, upgrades plan, or an explicit alternative enforcement decision is recorded
- source: GitHub API branch protection check on 2026-03-24 returned HTTP 403 upgrade/public requirement
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: https://github.com/Oscarling/openclaw-team/issues/8
- evidence: Repository visibility changed to `PUBLIC`, `gh repo view Oscarling/openclaw-team` confirms `visibility=PUBLIC`, and branch protection was then applied successfully on the default branch
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-007
- title: Normalize remote default branch naming from codex/next-task to main
- type: debt
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-003
- start_when: The current stacked PR flow is stable enough to retarget or rename the default branch without unnecessary churn
- done_when: The remote default branch is `main` and review, CI, and protection settings are aligned with that name
- source: GitHub repository snapshot on 2026-03-24 shows default branch `codex/next-task` even after public visibility and branch protection setup
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: https://github.com/Oscarling/openclaw-team/issues/9
- evidence: Remote `main` now matches `codex/next-task`, GitHub default branch is `main`, branch protection is enabled on `main`, and PRs #1 and #2 now target `main`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-008
- title: Finalize the long-term single-maintainer branch protection policy
- type: debt
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-003
- start_when: The repository owner confirms there is only one human maintainer and wants GitHub policy to match the actual operating model
- done_when: `main` enforces PR-based changes, strict CI, conversation resolution, and admin enforcement with `required_approving_review_count=0` until a second human maintainer actually joins
- source: User clarification on 2026-03-24 that the project currently has one human maintainer only and AI assistance does not count as a second reviewer
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: -
- evidence: `gh api repos/Oscarling/openclaw-team/branches/main/protection` now reports `required_approving_review_count=0`, `enforce_admins.enabled=true`, required checks `baseline-tests`/`shell-checks`, and required conversation resolution enabled
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-009
- title: Revisit reviewer-count enforcement if a second human maintainer joins
- type: future
- status: planned
- phase: later
- priority: p3
- owner: Oscarling
- depends_on: BL-20260324-008
- start_when: A second human maintainer is actively landing changes and can perform independent code review
- done_when: Branch protection is recalibrated to require non-zero human approvals and the governance docs are updated to match
- source: Single-maintainer policy finalization on 2026-03-24
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: deferred:activate-when-second-human-maintainer-joins
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-010
- title: Harden Trello read-only ingress with dependency-safe tests
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-005
- start_when: Governance gates are live on `main` and the next mainline step needs a safer, testable Trello read-only entry before more real smokes
- done_when: `skills/trello_readonly_prep.py` and the Trello read-only ingestion path can be tested without a hard `requests` import dependency, new unit coverage is enforced in local premerge and CI, and the current-state ledger reflects the hardened path
- source: Post-governance backlog sweep on 2026-03-24 identified that the Trello read-only entry path has no dedicated unit coverage and still relies on a hard `requests` import
- link: /Users/lingguozhong/openclaw-team/TRELLO_READONLY_INGRESS_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/15
- evidence: `TRELLO_READONLY_INGRESS_HARDENING_REPORT.md` records the hardening pass; `tests/test_trello_readonly_ingress.py` was added; `scripts/premerge_check.sh` and `.github/workflows/ci.yml` now enforce that coverage; local validation passed for backlog lint/sync plus the new Trello and existing finalization tests
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-011
- title: Run a governed real Trello read-only smoke through preview generation
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-010
- start_when: Trello read-only ingress hardening is merged and the runtime environment still exposes valid read-only credentials
- done_when: A real Trello read-only run is executed under the pre-run gate, the outcome is captured in a repo evidence report, and the current-state ledger truthfully records whether the live run created a new preview or was blocked by dedupe/runtime state
- source: Standard post-merge flow on 2026-03-24 after BL-20260324-010 landed identified the next smallest mainline step as one real Trello read-only smoke to preview
- link: /Users/lingguozhong/openclaw-team/TRELLO_READONLY_PREVIEW_SMOKE_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/17
- evidence: `TRELLO_READONLY_PREVIEW_SMOKE_REPORT.md` records a real GET-only Trello smoke pass plus a preview-only ingest run with `processed=0`, `duplicate_skipped=4`, and `preview_created=0`; the live fetched cards were all already present in local dedupe history and one extra duplicate came from `trello_readonly_mapped_sample.json` being recovered from `processing/`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-012
- title: Stop trello_readonly_prep smoke output from polluting the live processing queue
- type: debt
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-011
- start_when: The real preview smoke has confirmed that `skills/trello_readonly_prep.py` still writes a recoverable sample file under `processing/`
- done_when: Running `skills/trello_readonly_prep.py --smoke-read` no longer creates recoverable live-queue input under `processing/`, the behavior is covered by tests, and one rerun of the governed Trello preview smoke confirms `processing_recovered=0`
- source: `TRELLO_READONLY_PREVIEW_SMOKE_REPORT.md` on 2026-03-24 showed `processing_recovered=1` because `trello_readonly_mapped_sample.json` was picked up during the real ingest run
- link: /Users/lingguozhong/openclaw-team/TRELLO_READONLY_PREP_QUEUE_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/20
- evidence: `TRELLO_READONLY_PREP_QUEUE_HARDENING_REPORT.md` records the default output-path change to `artifacts/trello_readonly_prep/trello_readonly_mapped_sample.json`, new regression tests in `tests/test_trello_readonly_ingress.py`, and a governed rerun smoke with `processing_recovered=0`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-013
- title: Document mandatory gstack checkpoint stages in the engineering workflow
- type: debt
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-001
- start_when: The repository owner wants gstack expert involvement to be institutionalized instead of remembered ad hoc
- done_when: The engineering workflow explicitly states when gstack checkpoints should be used and this rule is recorded in the current-state ledger
- source: User request on 2026-03-24 to clarify which project stages should involve gstack experts and to write that into backlog
- link: /Users/lingguozhong/openclaw-team/docs/ENGINEERING_WORKFLOW.md
- issue: -
- evidence: `docs/ENGINEERING_WORKFLOW.md` now includes a `Gstack Checkpoints` section covering phase planning, UI work, investigations, pre-merge review, ship/deploy closeout, and safety-sensitive runs, plus a rule to record either usage or explicit skip rationale
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-014
- title: Run a clean Trello preview-creation smoke against an unseen live card or scope
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-012, BL-20260324-015
- start_when: Prep-helper queue pollution is fixed and at least one approved live Trello card or scope is outside local dedupe history
- done_when: A governed real Trello preview smoke targets an unseen live card or narrower live scope and truthfully records whether a new preview is created
- source: `TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md` on 2026-03-24 recorded a list-scoped rerun against a fresh unseen card
- link: /Users/lingguozhong/openclaw-team/TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/22
- evidence: `TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md` records a governed list-scoped rerun with `preview_created=1`, `processing_recovered=0`, and preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de` created in pending-approval state
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-015
- title: Provide an unseen live Trello card or alternate live scope for the preview smoke
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: `BL-20260324-014` discovery has confirmed that the current configured board scope contains no unseen open cards outside local dedupe history
- done_when: At least one approved live Trello card or alternate board/list scope exists whose mapped origin id is not already present in local dedupe history and can be used for a governed rerun of `BL-20260324-014`
- source: User created a fresh live card on 2026-03-24 and `TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md` confirmed it was reachable in list `待办`
- link: /Users/lingguozhong/openclaw-team/TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/23
- evidence: `TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md` records the new card `trello:69c24cd3c1a2359ddd7a1bf8` in list `待办` with `open_list_cards=5`, `unseen_cards=1`, and a successful governed rerun that used that card to create a new preview
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-016
- title: Decide the disposition of the fresh Trello preview created by the governed smoke
- type: mainline
- status: done
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-014
- start_when: A fresh live Trello preview has been created in pending-approval state and the repo needs a standard-process decision on whether to stop at smoke evidence or open a new approval/execution phase
- done_when: The repo truthfully records one of two outcomes for preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de`: it either remains intentionally unapproved as smoke evidence, or a new governed phase is opened to review, approve, and execute it
- source: User asked on 2026-03-24 which standard-process path should be taken next if the order does not materially affect later work
- link: /Users/lingguozhong/openclaw-team/TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md
- issue: -
- evidence: `TRELLO_LIVE_PREVIEW_CREATION_SMOKE_REPORT.md` now records the default closeout path: preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de` is intentionally left unapproved as smoke evidence, and no approval/execute phase is opened automatically
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-017
- title: Review, explicitly approve, and run one governed execution of the fresh Trello preview
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-014, BL-20260324-016
- start_when: The user has explicitly chosen to continue beyond the smoke-evidence boundary and preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de` is still pending approval
- done_when: The repo truthfully records one explicit approval decision and one governed execution result for preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de`, without expanding scope into Git finalization or Trello Done
- source: User request on 2026-03-24 to continue after the smoke phase closeout
- link: /Users/lingguozhong/openclaw-team/TRELLO_LIVE_PREVIEW_EXECUTION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/27
- evidence: `TRELLO_LIVE_PREVIEW_EXECUTION_REPORT.md` records one explicit approval decision, one initial sandboxed execute failure before worker launch, one elevated replay in real mode, and the final governed result `rejected` with `critic_verdict=needs_revision`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-018
- title: Address the artifact-quality findings exposed by the governed fresh-preview execution
- type: debt
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-017
- start_when: The governed execution report has confirmed the control chain works, but the Critic still returned `needs_revision` for artifact-quality reasons
- done_when: The repo either fixes or intentionally accepts the fresh-review findings around output format fidelity, path portability, traceability, and runtime evidence expectations before another approval/execute attempt
- source: `TRELLO_LIVE_PREVIEW_EXECUTION_REPORT.md` on 2026-03-24 captured Critic findings about fake `.xlsx` output semantics, hardcoded input path, truncated description context, and missing runtime output evidence
- link: /Users/lingguozhong/openclaw-team/PREVIEW_ARTIFACT_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/29
- evidence: `PREVIEW_ARTIFACT_CONTRACT_HARDENING_REPORT.md` records the adapter-side hardening that preserves richer description context, steers automation toward `artifacts/scripts/pdf_to_excel_ocr.py`, and encodes explicit `.xlsx` fidelity plus no-hardcoded-input-path rules with regression tests
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-019
- title: Validate the hardened preview artifact contract on a fresh preview candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-018, BL-20260324-020
- start_when: The explicit same-origin regeneration path is merged and can produce a fresh governed preview candidate under the hardened source-side contract
- done_when: A governed validation phase proves whether the hardened contract clears the prior review findings on a fresh preview candidate, without guessing around dedupe-frozen runtime state
- source: `PREVIEW_ARTIFACT_CONTRACT_HARDENING_REPORT.md` on 2026-03-24 noted that the already-executed preview cannot inherit the new adapter contract and the current dedupe freeze blocks a simple same-origin re-preview
- link: /Users/lingguozhong/openclaw-team/HARDENED_PREVIEW_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/33
- evidence: `HARDENED_PREVIEW_VALIDATION_REPORT.md` records one real same-origin Trello regeneration using token `regen-20260324-bl019-001`, a fresh preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-18b3caaace36`, one explicit approval, and one real execute showing the prior four review findings were cleared even though the regenerated runner still ended with new `needs_revision` concerns
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-020
- title: Add an explicit controlled regeneration path for same-origin preview creation
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-018
- start_when: The hardened source-side contract is merged and the next governed step is to regenerate a preview for the same Trello origin instead of relying on a fresh-card path
- done_when: The ingest path preserves the default origin-based freeze, but a caller can intentionally provide an explicit regeneration token that creates one new auditable preview for the same origin under controlled conditions
- source: User request on 2026-03-24 to make an explicit `regeneration path` phase first, plus the future-upgrade clause in `BASELINE_FREEZE_NOTE.md` allowing `rerun/replay token` based re-entry
- link: /Users/lingguozhong/openclaw-team/PREVIEW_REGENERATION_PATH_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/31
- evidence: `PREVIEW_REGENERATION_PATH_REPORT.md` records the explicit `regeneration_token` path that preserves default `origin` freeze, adds governed `origin_regeneration:<origin_id>:<token>` dedupe for same-origin re-preview, updates `BASELINE_FREEZE_NOTE.md`, and passes phase-local smoke/regressions plus `backlog_lint`, `backlog_sync`, and `premerge_check`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-021
- title: Address residual inbox-runner contract gaps exposed by BL-20260324-019 validation
- type: debt
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-019
- start_when: The BL-20260324-019 validation report has confirmed the original four findings are cleared, but the regenerated runner still returns `needs_revision` for status-model, path-resolution, readonly-enforcement, and zero-input-behavior concerns
- done_when: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` emits reviewable `partial` outcomes for dry-run and zero-input conditions, resolves its delegate relative to the repo instead of `Path.cwd()`, enforces the intended readonly delegate contract, and is covered by focused regression tests plus a new hardening report before another governed validation or production use
- source: `HARDENED_PREVIEW_VALIDATION_REPORT.md` on 2026-03-24 recorded new review concerns after the regenerated same-origin validation execute
- link: /Users/lingguozhong/openclaw-team/INBOX_RUNNER_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/35
- evidence: `INBOX_RUNNER_CONTRACT_HARDENING_REPORT.md` records the runner hardening that adds reviewable `partial` outcomes, repo-root delegate resolution, reviewed-script enforcement, focused regression coverage, and passing local gates through `bash scripts/premerge_check.sh`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-022
- title: Propagate BL-20260324-021 runner hardening into the source-side preview contract
- type: debt
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-021
- start_when: `BL-20260324-021` has hardened the current generated runner artifact, but the source-side preview contract still does not encode the new rules for reviewable partial outcomes, delegate path resolution, or reviewed-script delegation
- done_when: The source-side automation contract encodes the `BL-20260324-021` runner rules so future regenerated previews can inherit reviewable `partial` semantics, repo-root delegate resolution expectations, and reviewed-script delegation constraints before the next governed validation run
- source: `INBOX_RUNNER_CONTRACT_HARDENING_REPORT.md` on 2026-03-24 recorded that the current phase hardened the generated runner artifact itself, but did not yet push those rules back into the source-side preview contract
- link: /Users/lingguozhong/openclaw-team/INBOX_RUNNER_CONTRACT_PROPAGATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/37
- evidence: `INBOX_RUNNER_CONTRACT_PROPAGATION_REPORT.md` records the source-side contract propagation that adds reviewable partial-outcome, delegate-resolution, and reviewed-script delegation rules to `adapters/local_inbox_adapter.py`, gates `tests/test_local_inbox_adapter.py` in local/CI merge checks, and passes `bash scripts/premerge_check.sh`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-023
- title: Validate the propagated runner contract on a fresh preview candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-020, BL-20260324-022
- start_when: `BL-20260324-022` is merged and the controlled same-origin regeneration path is still available, so a fresh preview candidate can be created under the propagated source-side runner contract
- done_when: One governed validation phase creates a fresh same-origin preview candidate under the propagated runner contract, runs one explicit approval plus one real execute, and records whether Critic now passes or still returns `needs_revision` without expanding scope into Git finalization or Trello Done
- source: `INBOX_RUNNER_CONTRACT_PROPAGATION_REPORT.md` on 2026-03-24 concluded that the next correct step is another governed validation phase that exercises a preview candidate under the propagated source-side contract
- link: /Users/lingguozhong/openclaw-team/PROPAGATED_RUNNER_CONTRACT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/39
- evidence: `PROPAGATED_RUNNER_CONTRACT_VALIDATION_REPORT.md` records one real same-origin Trello regeneration using token `regen-20260324-bl023-001`, a fresh preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-92872bb091b6`, one explicit approval, and one real execute showing the propagated contract did reach the fresh candidate even though the run still ended with a new `needs_revision` set
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-024
- title: Address residual delegate-evidence and robustness gaps exposed by BL-20260324-023 validation
- type: debt
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-023
- start_when: `BL-20260324-023` has validated that the propagated runner contract reaches a fresh preview candidate, but the governed execute still returns `needs_revision` because the generated runner leaves gaps around delegate evidence visibility, stronger success evidence, traceability fidelity, or subprocess timeout handling
- done_when: The repo either resolves or explicitly accepts the residual delegate-evidence and robustness review gaps before another governed validation or production use of the generated inbox runner
- source: `PROPAGATED_RUNNER_CONTRACT_VALIDATION_REPORT.md` on 2026-03-24 will record the post-propagation governed execute result and the remaining Critic concerns
- link: /Users/lingguozhong/openclaw-team/POST_PROPAGATION_RUNNER_GAP_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/41
- evidence: `POST_PROPAGATION_RUNNER_GAP_HARDENING_REPORT.md` records the source-side contract hardening that preserves richer automation description context, keeps `artifacts/scripts/pdf_to_excel_ocr.py` in execute-time critic scope, requires stronger delegate success evidence, adds delegate timeout handling, and passes `bash scripts/premerge_check.sh`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-025
- title: Validate BL-20260324-024 hardening on a fresh same-origin preview candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-024
- start_when: `BL-20260324-024` is merged so the tightened description-fidelity, delegate-evidence, review-scope, and timeout rules can be tested through the normal governed preview pipeline
- done_when: One governed validation creates a fresh same-origin preview candidate after the BL-20260324-024 hardening, runs one explicit approval plus one real execute, and records whether the new live-generated runner clears the post-propagation residual review concerns or exposes a smaller new set
- source: `POST_PROPAGATION_RUNNER_GAP_HARDENING_REPORT.md` on 2026-03-24 concludes the next correct step is another governed validation on a fresh same-origin candidate rather than mutating the hardening phase
- link: /Users/lingguozhong/openclaw-team/POST_PROPAGATION_HARDENING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/43
- evidence: `POST_PROPAGATION_HARDENING_VALIDATION_REPORT.md` records one real same-origin Trello regeneration using token `regen-20260324-bl025-001`, a fresh preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-19461fb0341a`, one explicit approval, and one real execute showing the BL-20260324-024 hardening did reach the fresh candidate even though automation then failed with repeated `The read operation timed out`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-026
- title: Stabilize automation LLM read timeouts blocking post-hardening live validation
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-025
- start_when: `BL-20260324-025` has proved that the fresh preview candidate carries the BL-20260324-024 hardening, but the automation worker still fails real execute because the configured LLM endpoint times out before producing any script artifact
- done_when: The repo either mitigates the automation LLM read-timeout failure path or explicitly changes runtime/provider policy enough to let the next governed live validation reach artifact generation and review
- source: `POST_PROPAGATION_HARDENING_VALIDATION_REPORT.md` on 2026-03-24 records three consecutive automation LLM read timeouts at `https://fast.vpsairobot.com/v1/chat/completions`, which now block further governed validation
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_TIMEOUT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/45
- evidence: `AUTOMATION_TIMEOUT_HARDENING_REPORT.md` records the runtime fix that raises the default worker LLM read timeout to 120 seconds, exposes timeout/retry overrides through `ARGUS_LLM_TIMEOUT_SECONDS` and `ARGUS_LLM_MAX_RETRIES`, forwards those settings through `skills/delegate_task.py`, and passes focused regression coverage in `tests/test_argus_hardening.py`
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-027
- title: Validate BL-20260324-026 timeout mitigation on a fresh same-origin preview candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-026
- start_when: `BL-20260324-026` is merged so the relaxed default timeout policy can be exercised through the normal governed preview pipeline under real execution
- done_when: One governed validation creates a fresh same-origin preview candidate after the timeout hardening, runs one explicit approval plus one real execute, and records whether automation now reaches artifact generation and critic review under the new timeout policy
- source: `AUTOMATION_TIMEOUT_HARDENING_REPORT.md` on 2026-03-24 concludes the next correct step is a fresh governed validation rather than a same-preview replay
- link: /Users/lingguozhong/openclaw-team/POST_TIMEOUT_HARDENING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/47
- evidence: `POST_TIMEOUT_HARDENING_VALIDATION_REPORT.md` records one fresh same-origin regeneration (`regen-20260325-bl027-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-4ce6c1cce934`, explicit approval, and one governed real execute where automation `AUTO-20260325-854` and critic `CRITIC-20260325-275` both completed with runtime logs showing `timeout=120s, attempts=3`, confirming the timeout mitigation now reaches artifact generation and critic review
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-24

### BL-20260325-028
- title: Align generated inbox runner contract with delegate report schema and dry-run semantics
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-027
- start_when: `BL-20260324-027` confirms timeout hardening lets real governed runs reach automation and critic artifacts, exposing the remaining integration-level `needs_revision` concerns around wrapper/delegate contract alignment
- done_when: Source-side automation contract hints and constraints explicitly enforce reuse of the reviewed inbox runner behavior and delegate-report compatibility (including `total_files/status_counter/dry_run` semantics), focused tests cover the new contract requirements, and one evidence report records the phase outcome
- source: `POST_TIMEOUT_HARDENING_VALIDATION_REPORT.md` on 2026-03-25 records that automation and critic both completed under timeout hardening but critic still returned `needs_revision` due wrapper/delegate integration gaps
- link: /Users/lingguozhong/openclaw-team/RUNNER_CONTRACT_ALIGNMENT_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/49
- evidence: `RUNNER_CONTRACT_ALIGNMENT_REPORT.md` records source-side automation contract hardening in `adapters/local_inbox_adapter.py` (wrapper reuse preference, delegate schema/handoff guidance, explicit dry-run semantics), plus focused regressions in `tests/test_local_inbox_adapter.py` and `tests/test_trello_readonly_ingress.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-029
- title: Validate BL-20260325-028 contract alignment on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-028
- start_when: `BL-20260325-028` is merged so a fresh same-origin run can verify whether strengthened source-side contract guidance reduces integration-level `needs_revision` findings
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-028, runs one explicit approval plus one real execute, and records whether automation/critic outcome now clears the previously observed wrapper/delegate contract drift findings
- source: `RUNNER_CONTRACT_ALIGNMENT_REPORT.md` on 2026-03-25 concludes the next correct step is a fresh governed validation phase rather than assuming contract hardening success without runtime evidence
- link: /Users/lingguozhong/openclaw-team/POST_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/51
- evidence: `POST_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl029-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-ab85bf08e44d` with explicit approval and one real execute; automation (`AUTO-20260325-855`) and critic (`CRITIC-20260325-276`) both completed, and the run isolated a concrete blocker where the generated wrapper unconditionally passes `--report-json` but the reviewed delegate does not support that CLI argument, so integration remains `critic_verdict=needs_revision`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-030
- title: Fix wrapper/delegate report-handoff CLI mismatch exposed by BL-20260325-029
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-029
- start_when: `BL-20260325-029` has completed validation and narrowed the remaining `needs_revision` root cause to wrapper/delegate CLI contract drift around `--report-json` handoff
- done_when: Wrapper/delegate integration no longer passes unsupported CLI arguments, evidence handoff remains reviewable and deterministic (stdout JSON and/or sidecar path contract clearly aligned), focused tests cover the agreed contract, and one phase report records the implementation outcome
- source: `POST_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md` on 2026-03-25 confirms the post-BL-20260325-028 governed run still fails review because wrapper and delegate report-handoff CLI contracts are incompatible
- link: /Users/lingguozhong/openclaw-team/RUNNER_DELEGATE_CLI_ALIGNMENT_FIX_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/53
- evidence: `RUNNER_DELEGATE_CLI_ALIGNMENT_FIX_REPORT.md` records the delegate-side compatibility fix that adds optional `--report-json` support to `artifacts/scripts/pdf_to_excel_ocr.py`, unifies report emission via `emit_report(...)` across success/failure paths, adds focused regressions in `tests/test_pdf_to_excel_ocr_delegate.py`, and updates usage documentation so wrapper/delegate report handoff no longer relies on an undeclared CLI argument
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-031
- title: Validate BL-20260325-030 CLI alignment on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-030
- start_when: `BL-20260325-030` is merged so a fresh same-origin governed run can verify whether the delegate-side CLI alignment removes the remaining wrapper/delegate report-handoff rejection pattern under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-030, runs one explicit approval plus one real execute, and records whether automation/critic outcome now clears the `--report-json` compatibility blocker isolated in BL-20260325-029
- source: `RUNNER_DELEGATE_CLI_ALIGNMENT_FIX_REPORT.md` on 2026-03-25 concludes the next required step is governed runtime validation rather than assuming source-side fix success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_CLI_ALIGNMENT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/55
- evidence: `POST_CLI_ALIGNMENT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl031-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-6c674f5014a3` with explicit approval and one real execute; automation (`AUTO-20260325-856`) completed, critic (`CRITIC-20260325-277`) returned `needs_revision`, and runtime review isolated a new wrapper/delegate sidecar-flag mismatch (`--report-file` vs delegate `--report-json`) plus discovery-consistency concerns
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-032
- title: Re-align generated wrapper report-handoff flag and discovery contract after BL-20260325-031
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-031
- start_when: `BL-20260325-031` has completed and confirmed the end-to-end path still fails review because generated wrapper invocation drifted to `--report-file` while the reviewed delegate contract is `--report-json`
- done_when: Source-side/runtime contract hardening prevents wrapper-side report-flag drift against reviewed delegate CLI, wrapper/delegate PDF discovery semantics are aligned or explicitly justified in contract/tests, and one phase report records the implementation outcome with focused regressions
- source: `POST_CLI_ALIGNMENT_VALIDATION_REPORT.md` on 2026-03-25 confirms the fresh governed validation after BL-20260325-030 still yields `needs_revision` due wrapper-side report-handoff drift and discovery inconsistency
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_REPORT_FLAG_REALIGNMENT_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/57
- evidence: `WRAPPER_DELEGATE_REPORT_FLAG_REALIGNMENT_REPORT.md` records source-side hardening in `adapters/local_inbox_adapter.py` that adds explicit report-flag contract guidance (`--report-json` vs undeclared aliases), wrapper/delegate discovery-consistency guidance, and matching constraint/acceptance gates, with focused regression updates in `tests/test_local_inbox_adapter.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-033
- title: Validate BL-20260325-032 report-flag and discovery hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-032
- start_when: `BL-20260325-032` is merged so a fresh same-origin governed run can verify whether strengthened source-side contract guidance now prevents wrapper report-flag drift and discovery inconsistency under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-032, runs one explicit approval plus one real execute, and records whether automation/critic outcome now clears the `--report-file` vs `--report-json` and discovery-alignment findings observed in BL-20260325-031
- source: `WRAPPER_DELEGATE_REPORT_FLAG_REALIGNMENT_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming source-side contract hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_REPORT_FLAG_REALIGNMENT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/59
- evidence: `POST_REPORT_FLAG_REALIGNMENT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl033-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-2355ba57c8c0` with explicit approval and one real execute; automation (`AUTO-20260325-857`) succeeded with `--report-json` in wrapper summary while critic (`CRITIC-20260325-278`) still returned `needs_revision` because wrapper evidence snapshot was truncated for full-file validation
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-034
- title: Harden critic artifact snapshot completeness to avoid truncation-driven validation rejects
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-033
- start_when: `BL-20260325-033` has completed and confirmed the main runtime rejection shifted to critic-side truncated wrapper snapshot evidence rather than explicit report-flag mismatch
- done_when: Critic evidence handoff preserves complete wrapper artifact content (or equivalent complete review context) for generated script reviews, focused tests cover snapshot-size/completeness behavior, and one phase report records the hardening outcome
- source: `POST_REPORT_FLAG_REALIGNMENT_VALIDATION_REPORT.md` on 2026-03-25 records that fresh governed validation still returns `needs_revision` due critic-side truncated wrapper snapshot evidence
- link: /Users/lingguozhong/openclaw-team/CRITIC_SNAPSHOT_COMPLETENESS_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/61
- evidence: `CRITIC_SNAPSHOT_COMPLETENESS_HARDENING_REPORT.md` records hardening in `skills/execute_approved_previews.py` that raises and bounds critic artifact snapshot limits (default 120000 chars with env override), plus focused regressions in `tests/test_execute_approved_previews.py` covering both non-truncation under default policy and deterministic truncation when limits are intentionally lowered
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-035
- title: Validate BL-20260325-034 critic snapshot completeness hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-034
- start_when: `BL-20260325-034` is merged so a fresh same-origin governed run can verify whether increased critic snapshot completeness removes truncation-driven `needs_revision` outcomes under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-034, runs one explicit approval plus one real execute, and records whether critic can now complete full wrapper/delegate review without truncation-driven rejection
- source: `CRITIC_SNAPSHOT_COMPLETENESS_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming snapshot hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_CRITIC_SNAPSHOT_HARDENING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/63
- evidence: `POST_CRITIC_SNAPSHOT_HARDENING_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl035-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-103723900dc8` with explicit approval and one elevated real execute replay; automation (`AUTO-20260325-858`) and critic (`CRITIC-20260325-279`) both completed, critic still returned `needs_revision`, and the dominant blocker shifted from snapshot truncation to wrapper/delegate semantic alignment issues (zero-input status semantics, aggregate partial accounting, and explicit output-write attestation)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-036
- title: Harden wrapper/delegate semantic contract alignment after BL-20260325-035 runtime findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-035
- start_when: `BL-20260325-035` has completed and confirmed truncation is no longer the dominant blocker but runtime review still fails on wrapper/delegate semantic contract mismatches
- done_when: Delegate/wrapper contract is aligned on zero-input semantics and aggregate status truthfulness, delegate report includes explicit output-write evidence fields required for reviewability, focused tests cover the new semantics, and one hardening report records the outcome
- source: `POST_CRITIC_SNAPSHOT_HARDENING_VALIDATION_REPORT.md` on 2026-03-25 records `needs_revision` due semantic contract drift instead of snapshot truncation
- link: /Users/lingguozhong/openclaw-team/SEMANTIC_CONTRACT_ALIGNMENT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/65
- evidence: `SEMANTIC_CONTRACT_ALIGNMENT_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr.py` and `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` to align zero-input partial semantics, aggregate status truthfulness, and explicit output-write attestation (`excel_written`, `output_exists`, `output_size_bytes`), with focused regressions in `tests/test_pdf_to_excel_ocr_delegate.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-037
- title: Validate BL-20260325-036 semantic contract hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-036
- start_when: `BL-20260325-036` is merged so a fresh same-origin governed run can verify whether semantic contract hardening clears the remaining `needs_revision` blocker cluster under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-036, runs one explicit approval plus one real execute, and records whether runtime critic outcome now clears semantic contract mismatches found in BL-20260325-035
- source: `SEMANTIC_CONTRACT_ALIGNMENT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming semantic hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_SEMANTIC_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/67
- evidence: `POST_SEMANTIC_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl037-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-ad8052fe53ac` with explicit approval and one elevated real execute replay; runtime remained blocked by automation transport failure (`AUTO-20260325-859`, SSL EOF), so semantic hardening runtime effect stayed unverified
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-038
- title: Harden automation endpoint transport reliability after BL-20260325-037 SSL EOF blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-037
- start_when: `BL-20260325-037` has completed and confirmed governed replay is blocked by automation transport failure (`SSL: UNEXPECTED_EOF_WHILE_READING`) before artifact generation
- done_when: Automation LLM call path handles endpoint transport instability with deterministic retry/error classification hardening (or endpoint/TLS configuration hardening), focused tests cover the new behavior, and one blocker report records the implemented mitigation
- source: `POST_SEMANTIC_CONTRACT_ALIGNMENT_VALIDATION_REPORT.md` on 2026-03-25 records automation transport failure as the active blocker that prevented semantic runtime validation closure
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_ENDPOINT_SSL_RELIABILITY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/69
- evidence: `AUTOMATION_ENDPOINT_SSL_RELIABILITY_HARDENING_REPORT.md` records source-side hardening in `dispatcher/worker_runtime.py` and `skills/delegate_task.py` for deterministic transport error classification, endpoint-aware retry diagnostics, and optional fallback endpoint rotation (`ARGUS_LLM_FALLBACK_CHAT_URLS` / `ARGUS_LLM_FALLBACK_API_BASES`), with focused regression coverage in `tests/test_argus_hardening.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-039
- title: Validate BL-20260325-038 automation transport hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-038
- start_when: `BL-20260325-038` is merged so a fresh same-origin governed run can verify whether transport hardening clears SSL EOF-driven early automation failure
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-038, runs one explicit approval plus one real execute, and records whether runtime now reaches artifact generation and critic dispatch without transport-side SSL EOF blocker
- source: `AUTOMATION_ENDPOINT_SSL_RELIABILITY_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming transport hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_AUTOMATION_SSL_RELIABILITY_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/71
- evidence: `POST_AUTOMATION_SSL_RELIABILITY_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl039-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-055bd74afff8` with explicit approval and one elevated real execute replay; automation (`AUTO-20260325-860`) and critic (`CRITIC-20260325-280`) both completed, SSL EOF early-failure blocker did not recur, and dominant blocker shifted to generated wrapper success-evidence semantics
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-040
- title: Harden generated wrapper success-evidence contract after BL-20260325-039 runtime findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-039
- start_when: `BL-20260325-039` has completed and confirmed transport reliability blocker is cleared but runtime critic still returns `needs_revision` on generated wrapper success-evidence handling semantics
- done_when: Source-side/runtime contract hardening ensures generated wrapper success semantics cannot overclaim without explicit delegate output-write attestation consistency, focused tests cover the targeted semantics, and one blocker report records the hardening outcome
- source: `POST_AUTOMATION_SSL_RELIABILITY_VALIDATION_REPORT.md` on 2026-03-25 records that runtime progressed to critic review and shifted blocker to wrapper evidence-contract semantics
- link: /Users/lingguozhong/openclaw-team/WRAPPER_SUCCESS_EVIDENCE_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/73
- evidence: `WRAPPER_SUCCESS_EVIDENCE_CONTRACT_HARDENING_REPORT.md` records source-side contract hardening in `adapters/local_inbox_adapter.py` to require explicit delegate success attestation fields (`excel_written`, `output_exists`, `output_size_bytes`, and status-counter gates) with focused assertions in `tests/test_local_inbox_adapter.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-041
- title: Validate BL-20260325-040 wrapper success-evidence contract hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-040
- start_when: `BL-20260325-040` is merged so a fresh same-origin governed run can verify whether strengthened wrapper success-evidence contract guidance clears the new critic blocker cluster under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-040, runs one explicit approval plus one real execute, and records whether runtime critic outcome now clears wrapper success-evidence semantics findings from BL-20260325-039
- source: `WRAPPER_SUCCESS_EVIDENCE_CONTRACT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming contract hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_SUCCESS_EVIDENCE_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/75
- evidence: `POST_WRAPPER_SUCCESS_EVIDENCE_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl041-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-c19150aca7c7` with explicit approval and one elevated real execute replay; runtime remained blocked by automation endpoint authorization failure (`AUTO-20260325-861`, class `http_403`, `HTTP 403: Forbidden`) before critic dispatch, so BL-20260325-040 runtime effect remained unverified
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-042
- title: Harden automation endpoint authorization/runtime access after BL-20260325-041 HTTP 403 blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-041
- start_when: `BL-20260325-041` has completed and confirmed governed replay is blocked by automation endpoint authorization failure (`HTTP 403: Forbidden`) before artifact generation and critic dispatch
- done_when: Automation LLM path handles or avoids endpoint authorization/runtime-access blockers (credential/endpoint policy hardening with explicit diagnostics and deterministic behavior), focused tests cover the new behavior, and one blocker report records the implemented mitigation
- source: `POST_WRAPPER_SUCCESS_EVIDENCE_VALIDATION_REPORT.md` on 2026-03-25 records automation failure class `http_403` at `https://fast.vpsairobot.com/v1/chat/completions` as the active blocker that prevented runtime validation closure of BL-20260325-040
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_ENDPOINT_HTTP403_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/77
- evidence: `AUTOMATION_ENDPOINT_HTTP403_HARDENING_REPORT.md` records source-side hardening in `dispatcher/worker_runtime.py` that allows one bounded fallback-endpoint retry for primary-endpoint `http_401/http_403` authorization failures when fallback endpoints are configured, with focused regressions in `tests/test_argus_hardening.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-043
- title: Validate BL-20260325-042 HTTP 403 authorization hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-042
- start_when: `BL-20260325-042` is merged so a fresh same-origin governed run can verify whether authorization-fallback hardening restores automation artifact generation and critic dispatch under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-042, runs one explicit approval plus one real execute, and records whether runtime now clears the `http_403` automation blocker observed in BL-20260325-041
- source: `AUTOMATION_ENDPOINT_HTTP403_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming source-side auth-fallback hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_HTTP403_HARDENING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/79
- evidence: `POST_HTTP403_HARDENING_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl043-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-ddd178ff3fe9` with explicit approval and one elevated real execute replay; runtime confirmed BL-20260325-042 auth-fallback behavior (primary `http_403` triggered one bounded fallback retry to `https://api.openai.com/v1/chat/completions`), but run still failed before critic dispatch due fallback `tls_eof` plus final primary `http_403`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-044
- title: Harden multi-endpoint automation runtime policy after BL-20260325-043 mixed auth/transport blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-043
- start_when: `BL-20260325-043` has completed and confirmed auth-fallback retry now executes but governed run still fails before critic dispatch because primary endpoint remains `http_403` while fallback endpoint fails `tls_eof`
- done_when: Automation endpoint policy/runtime handling is hardened so governed execute has at least one reliable authorized endpoint path (with deterministic endpoint-order policy and explicit diagnostics), focused tests cover the mixed auth/transport failure path, and one blocker report records the mitigation
- source: `POST_HTTP403_HARDENING_VALIDATION_REPORT.md` on 2026-03-25 records the new mixed blocker pattern (`primary=http_403`, `fallback=tls_eof`) after BL-20260325-042 behavior activation
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_MULTI_ENDPOINT_POLICY_HARDENING_REPORT.md
- issue: -
- evidence: `AUTOMATION_MULTI_ENDPOINT_POLICY_HARDENING_REPORT.md` records source-side hardening in `dispatcher/worker_runtime.py` that quarantines authorization-failed endpoints for the remainder of a call after auth-fallback activation, preventing deterministic retry rotation back to known-`http_403` primary endpoints, with focused mixed-failure regression coverage in `tests/test_argus_hardening.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-045
- title: Validate BL-20260325-044 multi-endpoint runtime policy hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-044
- start_when: `BL-20260325-044` is merged so a fresh same-origin governed run can verify whether endpoint quarantine policy prevents same-call return to known-`http_403` primary endpoint and improves progression toward artifact generation and critic dispatch
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-044, runs one explicit approval plus one real execute, and records whether runtime now avoids same-call primary-endpoint `http_403` re-entry after auth-fallback activation
- source: `AUTOMATION_MULTI_ENDPOINT_POLICY_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_MULTI_ENDPOINT_POLICY_HARDENING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/82
- evidence: `POST_MULTI_ENDPOINT_POLICY_HARDENING_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl045-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-ba935bd928da` with explicit approval and one elevated real execute replay; runtime confirmed BL-20260325-044 endpoint-quarantine behavior activation during auth-failure retry flow and progressed to both automation artifact generation and critic dispatch (`AUTO-20260325-863` and `CRITIC-20260325-281`), with final decision `critic_verdict=needs_revision`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-046
- title: Harden wrapper success/partial evidence semantics after BL-20260325-045 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-045
- start_when: `BL-20260325-045` has completed and runtime has progressed to critic review with `needs_revision` findings focused on wrapper/delegate success-vs-partial evidence semantics rather than endpoint-policy pre-critic failures
- done_when: Source-side contract hardening aligns wrapper verdict behavior with best-effort evidence-backed partial semantics (without over-claiming success or over-failing reviewable partial outcomes), focused tests cover the targeted semantics, and one blocker report records the mitigation
- source: `POST_MULTI_ENDPOINT_POLICY_HARDENING_VALIDATION_REPORT.md` on 2026-03-25 records that multi-endpoint policy blocker is no longer dominant in the governed run and the next blocker is critic-identified wrapper/delegate evidence semantics
- link: /Users/lingguozhong/openclaw-team/WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/84
- evidence: `WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_HARDENING_REPORT.md` records source-side contract hardening in `adapters/local_inbox_adapter.py` that explicitly distinguishes wrapper success-only evidence gates from contract-compliant partial outcomes, adds partial-evidence guidance and next-step requirements, and is covered by focused regressions in `tests/test_local_inbox_adapter.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-047
- title: Validate BL-20260325-046 wrapper partial-evidence semantics hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-046
- start_when: `BL-20260325-046` is merged so a fresh same-origin governed run can verify whether updated wrapper contract semantics reduce recurrence of critic findings around success-vs-partial evidence handling under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-046, runs one explicit approval plus one real execute, and records whether critic findings shift away from wrapper partial-evidence semantics
- source: `WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming source-side semantic hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/86
- evidence: `POST_WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl047-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-4400266913e0` with explicit approval and one elevated real execute replay; runtime confirmed BL-20260325-046 wrapper partial-evidence hardening text is active in automation task inputs, while critic findings shifted to delegate-side OCR/status/reporting evidence quality (`CRITIC-20260325-282`, verdict `needs_revision`)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-048
- title: Harden delegate OCR/status reporting semantics after BL-20260325-047 critic blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-047
- start_when: `BL-20260325-047` has completed and confirmed critic focus has shifted from wrapper partial-evidence semantics to delegate-side OCR/status/reporting evidence quality under real execute
- done_when: Source-side delegate/report hardening ensures OCR/status outcomes remain truthful and evidence-rich for best-effort readonly flows, focused tests cover the targeted semantics, and one blocker report records the mitigation
- source: `POST_WRAPPER_PARTIAL_EVIDENCE_SEMANTICS_VALIDATION_REPORT.md` on 2026-03-25 records the remaining dominant blocker as delegate-side OCR/status/report evidence quality after BL-20260325-046 activation
- link: /Users/lingguozhong/openclaw-team/DELEGATE_OCR_STATUS_REPORTING_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/88
- evidence: `DELEGATE_OCR_STATUS_REPORTING_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr.py` that preserves truthful per-file status semantics for mixed extraction outcomes and enriches delegate JSON evidence (`files`, `notes`, `next_steps`), with focused regressions in `tests/test_pdf_to_excel_ocr_script.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-049
- title: Validate BL-20260325-048 delegate OCR/status reporting hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-048
- start_when: `BL-20260325-048` is merged so a fresh same-origin governed run can verify whether updated delegate OCR/status/report semantics reduce recurrence of critic findings under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-048, runs one explicit approval plus one real execute, and records whether critic findings shift away from delegate OCR/status/reporting evidence quality
- source: `DELEGATE_OCR_STATUS_REPORTING_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming delegate-hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_DELEGATE_OCR_STATUS_REPORTING_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/90
- evidence: `POST_DELEGATE_OCR_STATUS_REPORTING_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl049-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-e33731f048be` with explicit approval and elevated replay; runtime confirmed BL-20260325-048 delegate OCR/status/reporting hardening is active (`AUTO-20260325-865` succeeded) while critic findings shifted away from delegate evidence semantics to wrapper-level provenance/path traceability concerns (`CRITIC-20260325-283`, verdict `needs_revision`)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-050
- title: Harden wrapper provenance/path traceability semantics after BL-20260325-049 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-049
- start_when: `BL-20260325-049` confirms delegate-side OCR/status/report semantics are no longer the dominant blocker and critic focus has shifted to wrapper-level provenance/path/readonly traceability concerns under real execute
- done_when: Source-side wrapper hardening removes path-resolution ambiguity, strengthens provenance and readonly traceability attestations, and one blocker report records mitigation with focused tests
- source: `POST_DELEGATE_OCR_STATUS_REPORTING_VALIDATION_REPORT.md` on 2026-03-25 records the next required phase as wrapper-level provenance/path traceability hardening after delegate evidence semantics were validated
- link: /Users/lingguozhong/openclaw-team/WRAPPER_PROVENANCE_PATH_TRACEABILITY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/92
- evidence: `WRAPPER_PROVENANCE_PATH_TRACEABILITY_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` that enforces deterministic repo-root delegate path resolution, adds explicit provenance and readonly traceability attestation fields, and is covered by focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-051
- title: Validate BL-20260325-050 wrapper provenance/path traceability hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-050
- start_when: `BL-20260325-050` is merged so a fresh same-origin governed run can verify whether wrapper provenance/path/readonly traceability hardening reduces recurrence of critic findings under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-050, runs one explicit approval plus one real execute, and records whether critic findings shift away from wrapper provenance/path traceability concerns
- source: `WRAPPER_PROVENANCE_PATH_TRACEABILITY_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation rather than assuming wrapper hardening success without live evidence
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_PROVENANCE_PATH_TRACEABILITY_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/94
- evidence: `POST_WRAPPER_PROVENANCE_PATH_TRACEABILITY_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl051-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-58e83a71aacc` with explicit approval and real execute replays; phase remained pre-critic due automation runtime endpoint/auth failures (`AUTO-20260325-866`, `http_520` then `http_401`), so critic-shift outcome was inconclusive and a new automation runtime blocker was queued
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-052
- title: Harden automation endpoint/auth runtime resilience after BL-20260325-051 pre-critic blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-051
- start_when: `BL-20260325-051` confirms fresh governed validation cannot reach critic dispatch because automation fails pre-critic with endpoint/auth runtime failures (`http_520` and `http_401`)
- done_when: Source-side automation runtime hardening improves endpoint/auth handling so one governed execute can reliably progress beyond automation dispatch under the active environment profile, and one blocker report records mitigation with focused tests
- source: `POST_WRAPPER_PROVENANCE_PATH_TRACEABILITY_VALIDATION_REPORT.md` on 2026-03-25 records that BL-050 validation remained inconclusive due pre-critic automation endpoint/auth runtime failures
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/96
- evidence: `AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_HARDENING_REPORT.md` records source-side hardening in `dispatcher/worker_runtime.py` that classifies upstream `http_520-524` as retryable transient failures and preserves auth-fallback quarantine flow, with focused regressions in `tests/test_argus_hardening.py` covering `http_520 -> http_401 -> recovery` behavior
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-053
- title: Validate BL-20260325-052 automation endpoint/auth runtime resilience hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-052
- start_when: `BL-20260325-052` is merged so a fresh same-origin governed run can verify whether automation now progresses beyond pre-critic endpoint/auth blockers under real execute
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-052, runs one explicit approval plus one real execute, and records whether runtime reaches critic dispatch more reliably
- source: `AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/98
- evidence: `POST_AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl053-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a`; runtime confirmed BL-052 logic is active (`http_520` became retryable with fallback/auth-quarantine flow), but final attempt still failed pre-critic on timeout (`AUTO-20260325-867`), so a timeout-resilience blocker was queued
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-054
- title: Harden automation timeout/runtime reliability after BL-20260325-053 pre-critic timeout blocker
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-053
- start_when: `BL-20260325-053` confirms endpoint/auth recovery progresses further but governed execute still ends pre-critic on terminal timeout at the primary endpoint
- done_when: Source-side automation runtime hardening reduces timeout-induced pre-critic exhaustion and one blocker report records mitigation with focused tests
- source: `POST_AUTOMATION_ENDPOINT_AUTH_RUNTIME_RESILIENCE_VALIDATION_REPORT.md` on 2026-03-25 records timeout reliability as the dominant unresolved pre-critic blocker after BL-052 activation
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/100
- evidence: `AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_HARDENING_REPORT.md` records source-side runtime hardening in `dispatcher/worker_runtime.py` that grants one configurable terminal timeout recovery retry before exhaustion, with focused regressions in `tests/test_argus_hardening.py` covering both default recovery (`520 -> 401 -> timeout -> recovery`) and explicit disable (`ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES=0`)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-055
- title: Validate BL-20260325-054 automation timeout/runtime reliability hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-054
- start_when: `BL-20260325-054` is merged so a fresh same-origin governed run can verify whether timeout-resilience hardening consistently reaches critic dispatch after endpoint/auth recovery
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-054, runs one explicit approval plus one real execute, and records whether runtime now reaches critic dispatch without timeout exhaustion
- source: `AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/102
- evidence: `POST_AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl055-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-206313e36a04`; elevated execute reached both automation (`AUTO-20260325-868`) and critic (`CRITIC-20260325-284`) without terminal timeout exhaustion, validating BL-054 progression, while final verdict remained `needs_revision` on wrapper dry-run propagation semantics
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-056
- title: Harden wrapper dry-run delegate propagation semantics after BL-20260325-055 critic needs_revision verdict
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-055
- start_when: `BL-20260325-055` confirms timeout/runtime reliability hardening reaches critic dispatch, and critic returns `needs_revision` that wrapper/delegate dry-run semantics are not preserved end-to-end
- done_when: Source-side wrapper hardening ensures dry-run semantics are propagated consistently to the reviewed delegate path, and one blocker report records mitigation with focused tests
- source: `POST_AUTOMATION_TIMEOUT_RUNTIME_RELIABILITY_VALIDATION_REPORT.md` on 2026-03-25 records critic verdict `needs_revision` citing missing dry-run forwarding in the wrapper/delegate pair
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DRYRUN_DELEGATE_PROPAGATION_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/104
- evidence: `WRAPPER_DRYRUN_DELEGATE_PROPAGATION_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` that forwards `--dry-run` through the delegate path and preserves partial semantics from delegate dry-run evidence, with focused regression coverage in `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-057
- title: Validate BL-20260325-056 wrapper dry-run delegate propagation hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-056
- start_when: `BL-20260325-056` is merged so a fresh same-origin governed run can verify whether critic no longer flags wrapper/delegate dry-run propagation semantics
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-056, runs one explicit approval plus one real execute, and records whether critic findings move away from dry-run propagation concerns
- source: `WRAPPER_DRYRUN_DELEGATE_PROPAGATION_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DRYRUN_DELEGATE_PROPAGATION_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/107
- evidence: `POST_WRAPPER_DRYRUN_DELEGATE_PROPAGATION_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl057-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-d472aab5e3bf`; runtime reached automation (`AUTO-20260325-869`) and critic (`CRITIC-20260325-285`) without pre-critic timeout blockers, but critic still returned `needs_revision` citing unresolved wrapper/delegate contract gaps (dry-run propagation recurrence plus stdout-over-sidecar evidence precedence risk)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-058
- title: Harden wrapper/delegate evidence handoff contract to eliminate dry-run propagation recurrence and sidecar precedence risk
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-057
- start_when: `BL-20260325-057` confirms governed runtime reaches critic dispatch but critic still reports `needs_revision` on wrapper/delegate dry-run semantics recurrence and stdout-over-sidecar report precedence risk
- done_when: Source-side hardening ensures reviewed wrapper behavior is preserved under governed generation (dry-run delegate propagation and sidecar-first evidence handoff), and one blocker report records mitigation with focused tests
- source: `POST_WRAPPER_DRYRUN_DELEGATE_PROPAGATION_VALIDATION_REPORT.md` on 2026-03-25 records critic `needs_revision` persisted on wrapper/delegate contract handling despite BL-056 source merge
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/109
- evidence: `WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` and `adapters/local_inbox_adapter.py` to enforce dry-run delegation and sidecar-first report truth, with focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py` and updated adapter contract coverage in `tests/test_local_inbox_adapter.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-059
- title: Validate BL-20260325-058 wrapper/delegate evidence handoff contract hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-058
- start_when: `BL-20260325-058` is merged so a fresh same-origin governed run can verify whether critic findings move away from dry-run recurrence and sidecar precedence concerns
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-058, runs one explicit approval plus one real execute, and records whether critic findings no longer report wrapper/delegate evidence-handoff contract gaps
- source: `WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/111
- evidence: `POST_WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl059-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-d91793a3e34b`; runtime reached automation (`AUTO-20260325-870`) and critic (`CRITIC-20260325-286`) with final verdict `needs_revision`, while critic focus moved away from BL-058 target gaps (dry-run recurrence and sidecar precedence) toward readonly-semantics/OCR-sufficiency contract concerns
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-060
- title: Harden wrapper/delegate readonly semantics and OCR sufficiency contract after BL-20260325-059 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-059
- start_when: `BL-20260325-059` confirms prior evidence-handoff blocker gaps no longer dominate and critic `needs_revision` has shifted to readonly-contract semantics ambiguity plus OCR sufficiency evidence strictness concerns
- done_when: Source-side contract hardening aligns wrapper/delegate readonly semantics and runtime-summary wording with actual behavior, strengthens OCR sufficiency disclosure/gating expectations for best-effort readonly flows, and one blocker report records mitigation with focused tests
- source: `POST_WRAPPER_DELEGATE_EVIDENCE_HANDOFF_CONTRACT_VALIDATION_REPORT.md` on 2026-03-25 records critic focus moved from dry-run/sidecar gaps to readonly/OCR-sufficiency contract concerns
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/113
- evidence: `WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_HARDENING_REPORT.md` records source-side hardening in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` and `adapters/local_inbox_adapter.py` that clarifies readonly semantics as no-external-writeback scope and enforces conservative partial handling when delegate reports `ocr_runtime_status=blocked|partial` under `ocr=auto|on`, with focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py` and `tests/test_local_inbox_adapter.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-061
- title: Validate BL-20260325-060 readonly/OCR sufficiency contract hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-060
- start_when: `BL-20260325-060` is merged so a fresh same-origin governed run can verify whether critic findings move away from readonly-semantics and OCR-sufficiency contract concerns
- done_when: One governed validation creates a fresh same-origin preview candidate after BL-20260325-060, runs one explicit approval plus one real execute, and records whether critic findings no longer cite readonly/OCR sufficiency contract gaps
- source: `WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation under real execute conditions
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/115
- evidence: `POST_WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl061-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-0ceb21ad88dd`; runtime reached automation (`AUTO-20260325-871`) and critic (`CRITIC-20260325-287`) with final verdict `needs_revision`, while critic focus moved away from readonly/OCR-sufficiency concerns toward wrapper/delegate report-schema robustness and delegate-error surfacing gaps
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-062
- title: Harden wrapper/delegate report-schema robustness and delegate-error surfacing after BL-20260325-061 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-061
- start_when: `BL-20260325-061` confirms readonly/OCR sufficiency concerns are no longer dominant and critic `needs_revision` has shifted to report-schema consistency plus delegate-error surfacing gaps
- done_when: Source-side hardening normalizes delegate report schema across failure paths and ensures wrapper evidence/notes surface delegate error context explicitly, with focused tests and one blocker report
- source: `POST_WRAPPER_DELEGATE_READONLY_OCR_SUFFICIENCY_CONTRACT_VALIDATION_REPORT.md` on 2026-03-25 records the next blocker as wrapper/delegate report-schema robustness and diagnostic evidence surfacing
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/117
- evidence: `WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_HARDENING_REPORT.md` records schema normalization in `artifacts/scripts/pdf_to_excel_ocr.py` via shared report template across failure/no-input/normal exits and explicit delegate-error surfacing in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`, with focused regressions in `tests/test_pdf_to_excel_ocr_script.py` and `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-063
- title: Validate BL-20260325-062 report-schema diagnostic robustness hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-062
- start_when: `BL-20260325-062` is merged so one fresh governed candidate can verify critic findings move away from report-schema consistency and delegate-error surfacing gaps
- done_when: One governed validation run (smoke -> regeneration -> preview -> approval -> real execute) records whether critic findings no longer cite wrapper/delegate report-schema robustness and delegate-error diagnostic surfacing concerns
- source: `WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/119
- evidence: `POST_WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl063-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-6b1d3f094609`; runtime reached automation (`AUTO-20260325-872`) and critic (`CRITIC-20260325-288`) with final verdict `needs_revision`, while critic focus moved away from BL-062 report-schema/error-surfacing concerns toward output-boundary and aggregate outcome-contract clarity gaps
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-064
- title: Harden wrapper/delegate output-boundary policy and aggregate outcome-contract clarity after BL-20260325-063 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-063
- start_when: `BL-20260325-063` confirms critic focus has shifted away from report-schema/error-surfacing gaps to output-boundary and aggregate outcome-contract clarity concerns
- done_when: Source-side hardening constrains wrapper output destination policy for governed readonly runs, clarifies extraction-vs-export outcome semantics across wrapper/delegate reports, and records one blocker report with focused tests
- source: `POST_WRAPPER_DELEGATE_REPORT_SCHEMA_DIAGNOSTIC_ROBUSTNESS_VALIDATION_REPORT.md` on 2026-03-25 records the next blocker class as output-boundary and aggregate outcome-contract clarity
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/121
- evidence: `WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_HARDENING_REPORT.md` records wrapper output-boundary enforcement in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` (approved root: `artifacts/outputs`) and extraction/export phase-semantic hardening in `artifacts/scripts/pdf_to_excel_ocr.py`, with focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py` and `tests/test_pdf_to_excel_ocr_script.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-065
- title: Validate BL-20260325-064 output-boundary and outcome-contract hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-064
- start_when: `BL-20260325-064` is merged so one fresh governed candidate can verify critic findings move away from output-boundary and aggregate outcome-contract clarity concerns
- done_when: One governed validation run (smoke -> regeneration -> preview -> approval -> real execute) records whether critic findings no longer cite wrapper output-boundary policy and extraction-vs-export outcome-contract clarity gaps
- source: `WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/123
- evidence: `POST_WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl065-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-994e5ccbfd0b`; runtime reached automation (`AUTO-20260325-873`) and critic (`CRITIC-20260325-289`) with final verdict `needs_revision`, while critic focus moved away from output-boundary enforcement toward wrapper/delegate execution outcome-contract strictness and diagnostics completeness
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-066
- title: Harden wrapper/delegate execution outcome-contract strictness and diagnostics completeness after BL-065 critic findings
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-065
- start_when: `BL-20260325-065` confirms critic focus has shifted away from output-boundary policy to wrapper/delegate execution outcome semantics and diagnostic completeness gaps
- done_when: Source-side hardening makes wrapper subprocess exit-code handling deterministic (including non-zero with JSON evidence), canonicalizes no-input/partial/failed semantics across wrapper/delegate, preserves relevant stderr/stdout diagnostics in structured evidence, and records one blocker report with focused tests
- source: `POST_WRAPPER_DELEGATE_OUTPUT_BOUNDARY_OUTCOME_CONTRACT_VALIDATION_REPORT.md` on 2026-03-25 records the next blocker class as execution outcome-contract strictness and diagnostics completeness
- link: /Users/lingguozhong/openclaw-team/WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/125
- evidence: `WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_HARDENING_REPORT.md` records wrapper hardening in `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` for strict non-zero delegate exit handling, canonicalized partial/no-output semantics, and structured stdout/stderr diagnostics preservation, with focused regressions in `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-067
- title: Validate BL-20260325-066 execution outcome-contract and diagnostics hardening on a fresh same-origin governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-066
- start_when: `BL-20260325-066` is merged so one fresh governed candidate can verify critic findings move away from wrapper/delegate execution outcome semantics and diagnostics completeness concerns
- done_when: One governed validation run (smoke -> regeneration -> preview -> approval -> real execute) records whether critic findings no longer cite wrapper non-zero/partial semantics mismatches and diagnostics completeness gaps
- source: `WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_HARDENING_REPORT.md` on 2026-03-25 concludes the next required step is fresh governed runtime validation
- link: /Users/lingguozhong/openclaw-team/POST_WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/127
- evidence: `POST_WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_VALIDATION_REPORT.md` records one fresh same-origin governed run (`regen-20260325-bl067-001`) to preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153`; execution remained `rejected` because automation (`AUTO-20260325-874`) failed before critic dispatch with endpoint compatibility `http_400` at `https://aixj.vip/v1/chat/completions`, so BL-066 target finding shift stayed runtime-unverified
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-068
- title: Harden automation runtime endpoint/protocol compatibility for provider-backed LLM execution after BL-067 failures
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-067
- start_when: `BL-20260325-067` confirms governed execution is blocked before critic handoff by provider endpoint compatibility failures (`http_400`) in automation runtime
- done_when: Runtime/config hardening ensures automation worker can complete one real LLM call against declared provider settings (base URL + protocol + model mapping) without `http_400` contract mismatch, with focused tests and one blocker report
- source: `POST_WRAPPER_DELEGATE_EXECUTION_OUTCOME_DIAGNOSTIC_CONTRACT_VALIDATION_REPORT.md` on 2026-03-25 records endpoint/protocol/model compatibility as the next blocker class
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_RUNTIME_ENDPOINT_PROTOCOL_COMPATIBILITY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/129
- evidence: `AUTOMATION_RUNTIME_ENDPOINT_PROTOCOL_COMPATIBILITY_HARDENING_REPORT.md` records runtime wire-api hardening (`chat_completions`/`responses`/`auto`), delegate env propagation, and focused regressions (`tests/test_argus_hardening.py`), with one live replay showing terminal class moved from protocol mismatch `http_400` at `/chat/completions` to provider availability `http_502` at `/responses` (compatibility fallback active, blocker class shifted)
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-069
- title: Restore automation runtime provider availability/failover reliability after BL-068 protocol hardening
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-068
- start_when: `BL-20260325-068` is merged and replay evidence confirms protocol mismatch is mitigated while provider runtime remains blocked by `http_502` on responses endpoint before critic handoff
- done_when: Runtime failover configuration and execution path are verified by one governed real execute that reaches critic handoff without terminal provider availability failure at the initial endpoint
- source: `AUTOMATION_RUNTIME_ENDPOINT_PROTOCOL_COMPATIBILITY_HARDENING_REPORT.md` on 2026-03-25 confirms next blocker class is provider responses-endpoint availability/failover reliability
- link: /Users/lingguozhong/openclaw-team/AUTOMATION_RUNTIME_PROVIDER_AVAILABILITY_FAILOVER_COMPLETION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/131
- evidence: Iteration-1 hardening adds multi-candidate responses failover for `wire_api=auto` and new regression `test_call_llm_auto_fallback_tries_response_candidates_until_success`; completion replay using healthy backup provider endpoint reached full automation->critic handoff with `critic_verdict=pass` (`AUTO-20260325-874`, `CRITIC-20260325-290`) and final execute `processed`, with evidence archived in `runtime_archives/bl069/`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-070
- title: Validate BL-20260325-069 provider availability/failover hardening on one fresh governed candidate
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-069
- start_when: `BL-20260325-069` source-side failover hardening is merged so one fresh governed execute can confirm automation reaches critic handoff
- done_when: One governed validation run (smoke -> regeneration -> preview -> approval -> real execute) records critic handoff success and whether dominant findings move away from provider availability/failover failures
- source: `BL-20260325-069` is a blocker-hardening phase whose next required step is governed runtime validation on a fresh candidate
- link: /Users/lingguozhong/openclaw-team/POST_PROVIDER_AVAILABILITY_FAILOVER_GOVERNED_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/133
- evidence: `POST_PROVIDER_AVAILABILITY_FAILOVER_GOVERNED_VALIDATION_REPORT.md` records one fresh governed run (`regen-20260325-bl070-001`) creating preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-cb445a22289d`; elevated real execute reached automation (`AUTO-20260325-875`) and critic (`CRITIC-20260325-291`) with final decision `processed` / `critic_verdict=pass`, confirming BL-069 availability/failover hardening on a fresh candidate
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-071
- title: Stabilize governed execute provider profile selection to avoid manual desktop-secret dependency in BL-070 flow
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-070
- start_when: `BL-20260325-070` confirms fresh governed validation passes only after explicitly switching runtime env to a healthy backup provider profile
- done_when: Governed execute path can select an approved healthy provider profile from repository/runtime configuration without manual extraction of base URL/key from ad-hoc desktop files
- source: `POST_PROVIDER_AVAILABILITY_FAILOVER_GOVERNED_VALIDATION_REPORT.md` on 2026-03-25 shows BL-070 pass required manual backup profile injection from `~/Desktop/备用key.rtf`
- link: /Users/lingguozhong/openclaw-team/PROVIDER_PROFILE_SELECTION_STABILIZATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/135
- evidence: `skills/delegate_task.py` now supports profile-selected provider env assembly via `ARGUS_PROVIDER_PROFILE` and `ARGUS_PROVIDER_PROFILES_FILE` (with fail-closed key reference checks), `contracts/provider_profiles.example.json` defines non-secret profile structure, `tests/test_argus_hardening.py` adds three profile-selection regressions, and `bash scripts/premerge_check.sh` passed on 2026-03-25 with no failures
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-072
- title: Validate BL-20260325-071 provider-profile execute path on one governed replay without desktop-secret extraction
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-071
- start_when: `BL-20260325-071` is merged so execute runtime can select provider profile from config
- done_when: One governed replay execute (`--test-mode off --allow-replay`) runs with profile-selected provider config and archived evidence, without manual desktop-secret extraction during execution step
- source: `BL-20260325-071` completed source-side provider-profile selection hardening; next required step is governed replay validation using the new profile path
- link: /Users/lingguozhong/openclaw-team/POST_PROVIDER_PROFILE_GOVERNED_REPLAY_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/137
- evidence: One elevated governed replay on `preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153` ran with profile-selected config (`ARGUS_PROVIDER_PROFILE=bl072_fast_override`, `ARGUS_PROVIDER_PROFILES_FILE=/tmp/bl072_provider_profiles.json`) and archived evidence in `runtime_archives/bl072/`; runtime log confirms endpoint override from ambient `aixj.vip` to profile endpoint `https://fast.vpsairobot.com/v1/responses` (`wire_api=responses`), with terminal provider auth blocker `http_401` at `https://fast.vpsairobot.com/responses`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-073
- title: Restore provider credential/profile alignment so profile-selected governed execute can pass automation handoff
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-072
- start_when: BL-072 replay confirms profile-selection path is active but terminal failure class is provider authentication (`http_401`) under current key/profile pairing
- done_when: At least one approved provider profile + credential pairing is verified by live probe and governed replay to remove terminal auth failure as the dominant blocker class; if a new dominant blocker emerges, record evidence and queue next blocker
- source: `POST_PROVIDER_PROFILE_GOVERNED_REPLAY_VALIDATION_REPORT.md` on 2026-03-25 records profile override success but terminal `http_401` on fast provider responses endpoint
- link: /Users/lingguozhong/openclaw-team/POST_PROVIDER_CREDENTIAL_PROFILE_ALIGNMENT_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/139
- evidence: Backup profile/key pairing from `~/Desktop/备用key.rtf` was applied via runtime profile (`ARGUS_PROVIDER_PROFILE=bl073_fast_backup`) and probe matrix recorded `200` across `https://fast.vpsairobot.com/v1/responses` and `https://fast.vpsairobot.com/responses` for models `gpt-5.4`, `gpt-5-codex`, and `gpt-5`; governed replay on `preview-trello-69c24cd3c1a2359ddd7a1bf8-687ebc83a153` no longer failed with `http_401` and instead shifted dominant terminal class to `timeout` (`attempts=4/4`, endpoint `https://fast.vpsairobot.com/responses`) with evidence in `runtime_archives/bl073/`
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-074
- title: Stabilize aligned fast-provider runtime timeouts so governed replay can reach automation success
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-073
- start_when: BL-073 confirms auth blocker is removed but governed replay still terminates on timeout after retries under aligned profile/key pairing
- done_when: Timeout-stability replay attempts under aligned profile are executed and archived; if terminal timeout class is replaced by a new dominant upstream/gateway timeout class, record that shift and queue the next blocker
- source: `POST_PROVIDER_CREDENTIAL_PROFILE_ALIGNMENT_REPORT.md` on 2026-03-25 records probe `200` but execute terminal class shifted to timeout (`attempts=4/4`)
- link: /Users/lingguozhong/openclaw-team/POST_FAST_PROVIDER_TIMEOUT_STABILITY_VALIDATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/141
- evidence: Two elevated replay attempts under aligned fast-provider profile (`gpt-5.4` and `gpt-5`, tuned timeout/retry env) both ended with terminal class `http_524` at `https://fast.vpsairobot.com/responses` (`runtime_archives/bl074/tmp/bl074_execute_replay_tuned.json`, `runtime_archives/bl074/tmp/bl074_execute_replay_gpt5.json`), proving dominant blocker shifted from local timeout exhaustion to upstream gateway-timeout class while auth remained cleared
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25

### BL-20260325-075
- title: Harden fast-provider gateway-timeout resilience and timeout-recovery knob propagation for governed execute
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-074
- start_when: BL-074 confirms aligned profile no longer fails on auth but still terminates at `http_524` under replay attempts, and runtime indicates timeout-recovery retries knob is not propagated from execute env
- done_when: Delegate runtime receives explicit timeout-recovery override from execute env and governed replay validates gateway-timeout recovery extension behavior under aligned profile; if terminal `http_524` persists, archive evidence and queue the next blocker
- source: `POST_FAST_PROVIDER_TIMEOUT_STABILITY_VALIDATION_REPORT.md` on 2026-03-25 records dual-model tuned runs both ending at `http_524` and notes timeout-recovery env propagation gap
- link: /Users/lingguozhong/openclaw-team/FAST_PROVIDER_GATEWAY_TIMEOUT_RESILIENCE_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/143
- evidence: `skills/delegate_task.py` now propagates `ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES` into worker env, `dispatcher/worker_runtime.py` now applies timeout-recovery extension to `http_524` class (in addition to native timeout), and `tests/test_argus_hardening.py` adds focused coverage for both propagation and `http_524` recovery retries; governed replay evidence in `runtime_archives/bl075/` shows startup `timeout_recovery_retries=2` and two recovery extensions (`2 -> 3 -> 4` attempts) before terminal upstream `http_524`, so the next blocker remains provider gateway-timeout persistence
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-25

### BL-20260326-076
- title: Mitigate persistent upstream http_524 after timeout-recovery hardening to restore governed automation success
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-075
- start_when: BL-075 source hardening is merged and governed replay confirms timeout-recovery propagation/extension works (`attempts 2->4`) but still ends terminally on upstream `http_524`
- done_when: One governed replay under aligned fast-provider profile reaches automation success (and ideally critic handoff) without terminal `http_524` exhaustion, or conclusively validates an alternate stable provider path under the same governed contract
- source: `FAST_PROVIDER_GATEWAY_TIMEOUT_RESILIENCE_HARDENING_REPORT.md` on 2026-03-26 records propagation/resilience improvements but persistent terminal `http_524` at upstream endpoint
- link: /Users/lingguozhong/openclaw-team/PERSISTENT_HTTP524_PATH_MITIGATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/145
- evidence: `runtime_archives/bl076/tmp/bl076_probe_matrix.txt` confirmed `200` probes on `https://fast.vpsairobot.com/v1/{responses,chat/completions}` for models `gpt-5.4`, `gpt-5`, and `gpt-5-codex`; governed replay experiment A using profile `bl076_fast_chat` (`wire_api=chat_completions`, model `gpt-5-codex`) returned `processed=1` / `critic_verdict=pass` in `runtime_archives/bl076/tmp/bl076_execute_replay_experiment_a.json`, with automation and critic both `success` (`runtime_archives/bl076/runtime/*experiment-a*`, `runtime_archives/bl076/state/*`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-077
- title: Productize BL-076 validated chat path into repeatable governed provider-profile baseline
- type: mainline
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-076
- start_when: BL-076 confirms governed replay can pass via validated `chat_completions` path under aligned fast provider
- done_when: A repository-managed provider profile baseline (without ad-hoc temporary profile files) is documented and validated so future governed executes can reuse the BL-076 stable path with minimal manual runtime setup
- source: `PERSISTENT_HTTP524_PATH_MITIGATION_REPORT.md` on 2026-03-26 records a successful governed pass through temporary experiment profile `bl076_fast_chat`
- link: /Users/lingguozhong/openclaw-team/PROVIDER_PROFILE_BASELINE_PRODUCTIZATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/147
- evidence: Repository-managed `contracts/provider_profiles.json` now includes `fast_chat_governed_baseline` (`wire_api=chat_completions`, `api_key_env=OPENAI_API_KEY_FAST`), `tests/test_argus_hardening.py` adds coverage that default profile file resolution works without `ARGUS_PROVIDER_PROFILES_FILE`, and governed replay evidence in `runtime_archives/bl077/` confirms this repo profile path can complete (`runtime_archives/bl077/tmp/bl077_execute_replay_repo_profile_attempt_b.json`, `critic_verdict=pass`) without temporary profile files
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-078
- title: Stabilize repo-baseline governed replay reliability against intermittent upstream http_524
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-077
- start_when: BL-077 productizes and validates the repository-managed chat baseline path, but replay evidence still shows intermittent `http_524` failures before eventual pass
- done_when: Governed replay reliability under the repo baseline path is characterized and improved so at least one single-pass run can be expected without requiring immediate manual rerun after terminal `http_524`
- source: `PROVIDER_PROFILE_BASELINE_PRODUCTIZATION_REPORT.md` on 2026-03-26 records one first-attempt terminal `http_524` followed by a second-attempt pass under the same repo baseline profile
- link: /Users/lingguozhong/openclaw-team/SINGLE_PASS_RELIABILITY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/149
- evidence: `skills/execute_approved_previews.py` now adds one bounded in-process automation transient retry for class `http_524` (`ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS`, default 1), `tests/test_execute_approved_previews.py` adds focused coverage for retry-vs-no-retry behavior, and governed replay evidence in `runtime_archives/bl078/` confirms a single execute invocation under repo baseline profile completed `processed=1` / `critic_verdict=pass` without manual second command
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-079
- title: Observe and tune repo-baseline transient retry policy under repeated governed replays
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-078
- start_when: BL-078 merges and enables bounded in-process transient automation retry for `http_524`
- done_when: Multi-run governed evidence confirms whether current retry budget (default 1) is sufficient; if not, policy/knobs are tuned with archived evidence and focused tests
- source: `SINGLE_PASS_RELIABILITY_HARDENING_REPORT.md` on 2026-03-26 records single-pass success under new policy but still depends on upstream variability characteristics over time
- link: /Users/lingguozhong/openclaw-team/TRANSIENT_RETRY_POLICY_OBSERVATION_TUNING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/151
- evidence: `TRANSIENT_RETRY_POLICY_OBSERVATION_TUNING_REPORT.md` records multi-run governed observation in `runtime_archives/bl079/` (`bl079_replay_matrix_budget1*.tsv`), policy tuning in `skills/execute_approved_previews.py` expanding transient classes to `http_524/http_502/timeout`, focused regressions added in `tests/test_execute_approved_previews.py`, and a post-tune governed replay pass (`processed=1`, `critic_verdict=pass`) in `runtime_archives/bl079/tmp/bl079_replay_matrix_budget1_final.tsv`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-080
- title: Quantify retry-budget pass-rate and latency tradeoff for repo-baseline governed replay
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-079
- start_when: BL-079 lands expanded transient class coverage (`http_524/http_502/timeout`) and confirms at least one post-tune governed pass
- done_when: Controlled replay samples compare pass-rate and wall-time impact between retry budgets (`1` vs `2`) and freeze recommended default/profile guidance with archived evidence
- source: `TRANSIENT_RETRY_POLICY_OBSERVATION_TUNING_REPORT.md` on 2026-03-26 shows tuned transient-class coverage and a post-tune pass, but residual provider variability still leaves budget-vs-latency tradeoff unquantified
- link: /Users/lingguozhong/openclaw-team/RETRY_BUDGET_TRADEOFF_EVALUATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/153
- evidence: `RETRY_BUDGET_TRADEOFF_EVALUATION_REPORT.md` records controlled replay comparison in `runtime_archives/bl080/tmp/bl080_budget_tradeoff_matrix.tsv` (`budget=1` vs `2`), showing no processed pass-rate gain (`0/2` vs `0/2`) and a +79.6% average wall-time increase at budget `2` (174.0s -> 312.5s); `RUNTIME_CONTRACT.md` now freezes default guidance to keep `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-081
- title: Expand governed replay sample window for retry-budget policy confidence
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-080
- start_when: BL-080 freezes default budget guidance (`=1`) after short controlled sample comparison
- done_when: A larger, time-spread sample under fixed controls confirms whether temporary budget `2` windows ever produce meaningful processed pass-rate gains that justify latency cost, or closes the question and keeps default guidance unchanged
- source: `RETRY_BUDGET_TRADEOFF_EVALUATION_REPORT.md` on 2026-03-26 shows clear latency penalty at budget `2` but sample size remains small
- link: /Users/lingguozhong/openclaw-team/RETRY_BUDGET_CONFIDENCE_WINDOW_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/155
- evidence: `RETRY_BUDGET_CONFIDENCE_WINDOW_REPORT.md` records time-spread controlled matrix evidence in `runtime_archives/bl081/tmp/bl081_time_spread_matrix.tsv` (`s01-b1/s02-b2/s03-b1/s04-b2`) and combined confidence-window aggregation with `runtime_archives/bl080/tmp/bl080_budget_tradeoff_matrix.tsv`; combined results show `budget=2` limited pass-rate gain (`1/4`) but higher cost (`+32.9%` avg wall, `1.50` vs `0.75` avg retries), so default guidance remains `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-082
- title: Productize controlled budget-2 escalation trigger and replay runbook after confidence-window freeze
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-081
- start_when: BL-081 confirms default retry budget stays at `1` while budget `2` remains a temporary override path with mixed outcomes
- done_when: A documented, governed escalation trigger for temporary `budget=2` use (activation and rollback criteria) is added and validated by at least one archived drill run, so operators can use the override path consistently without drifting baseline defaults
- source: `RETRY_BUDGET_CONFIDENCE_WINDOW_REPORT.md` on 2026-03-26 shows occasional budget `2` benefit but persistent latency/retry overhead, requiring a stricter operational override playbook
- link: /Users/lingguozhong/openclaw-team/BUDGET2_ESCALATION_RUNBOOK_PRODUCTIZATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/157
- evidence: `RUNTIME_CONTRACT.md` now defines BL-082 governed activation/rollback/evidence rules for temporary `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=2`; drill run evidence is archived in `runtime_archives/bl082/tmp/bl082_drill_summary.tsv` and companion execute/runtime/state snapshots (`*drill-b2*`), validating runbook execution while preserving baseline default guidance (`=1`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-083
- title: Harden automation JSON-output validity recovery path after budget-2 drill failure signal
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-082
- start_when: BL-082 drill archives show a terminal automation failure containing `LLM output not valid JSON` under controlled replay
- done_when: Automation path adds bounded JSON-validity recovery/repair handling (with focused tests) and governed replay evidence confirms the new path improves completion robustness without relaxing baseline safety constraints
- source: `BUDGET2_ESCALATION_RUNBOOK_PRODUCTIZATION_REPORT.md` on 2026-03-26 records BL-082 drill rejection with terminal reason `LLM output not valid JSON`, indicating a remaining reliability blocker outside retry-budget policy
- link: /Users/lingguozhong/openclaw-team/JSON_OUTPUT_VALIDITY_RECOVERY_HARDENING_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/159
- evidence: `dispatcher/worker_runtime.py` now adds bounded JSON-output repair control (`ARGUS_LLM_JSON_REPAIR_ATTEMPTS`, default `1`, max `2`) with fail-closed fallback and repair telemetry (`metadata.json_output_repair_attempts_used`); focused regressions in `tests/test_argus_hardening.py` cover both successful one-shot repair and budget-zero fail-closed behavior; governed replay evidence in `runtime_archives/bl083/tmp/bl083_replay_summary.tsv` records `processed=1`, `critic_verdict=pass`, and `json_invalid_terminal=no`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-084
- title: Quantify JSON-repair path engagement and guardrail impact across time-spread governed replays
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-083
- start_when: BL-083 lands bounded JSON-output repair and single-run governed replay evidence under fixed controls
- done_when: A time-spread governed replay window measures how often JSON-repair is engaged (`json_output_repair_attempts_used`) and verifies that repair does not regress latency or verdict quality under baseline controls
- source: `JSON_OUTPUT_VALIDITY_RECOVERY_HARDENING_REPORT.md` on 2026-03-26 confirms BL-083 path correctness and one governed pass, but longer-window operational confidence for repair engagement frequency is still unquantified
- link: /Users/lingguozhong/openclaw-team/JSON_REPAIR_ENGAGEMENT_CONFIDENCE_WINDOW_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/161
- evidence: `JSON_REPAIR_ENGAGEMENT_CONFIDENCE_WINDOW_REPORT.md` records a 4-run time-spread governed matrix in `runtime_archives/bl084/tmp/bl084_json_repair_confidence_matrix.tsv`; measured JSON-repair engagement is `0/4`, terminal JSON-invalid failures are `0/4`, and dominant terminal class remains `timeout`, so baseline guidance is unchanged (`ARGUS_LLM_JSON_REPAIR_ATTEMPTS=1`, `ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS=1`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-085
- title: Targeted JSON-repair path exercise under controlled malformed-output replay to validate engaged-path quality
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-084
- start_when: BL-084 confirms time-spread production-like window has zero JSON-repair engagements and timeout-dominant failures
- done_when: A controlled malformed-output replay exercise triggers JSON-repair path deterministically, validates engaged-path verdict/latency behavior with archived evidence, and confirms no contract drift in output schema guarantees
- source: `JSON_REPAIR_ENGAGEMENT_CONFIDENCE_WINDOW_REPORT.md` on 2026-03-26 shows `json_output_repair_attempts_used` engagement `0/4`, so engaged-path operational quality still needs explicit controlled validation
- link: /Users/lingguozhong/openclaw-team/JSON_REPAIR_ENGAGED_PATH_CONTROLLED_REPLAY_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/163
- evidence: `JSON_REPAIR_ENGAGED_PATH_CONTROLLED_REPLAY_REPORT.md` records BL-085 controlled replay evidence in `runtime_archives/bl085/`; request trace `tmp/bl085_mock_requests.log` confirms deterministic sequence (`automation_initial_invalid -> automation_repair -> critic_pass`), automation output metadata records `json_output_repair_attempts_used=1`, and execute result reports `processed=1` with `critic_verdict=pass` while output schema contract remains stable
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-086
- title: Quantify timeout-dominant failure bottleneck across governed windows and codify mitigation priority
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-085
- start_when: BL-080/081/084 governed evidence repeatedly reports timeout-dominant failure classes, and BL-085 confirms JSON-repair engaged path itself is healthy under controlled replay
- done_when: A cross-window evidence report quantifies timeout share versus non-timeout classes using archived governed runs and records contract guidance that timeout mitigation remains higher priority than JSON-path tuning while timeout stays dominant
- source: `RETRY_BUDGET_CONFIDENCE_WINDOW_REPORT.md`, `JSON_REPAIR_ENGAGEMENT_CONFIDENCE_WINDOW_REPORT.md`, and `JSON_REPAIR_ENGAGED_PATH_CONTROLLED_REPLAY_REPORT.md` on 2026-03-26 indicate persistent timeout concentration after retry-budget and JSON-repair hardening
- link: /Users/lingguozhong/openclaw-team/TIMEOUT_BOTTLENECK_CONFIDENCE_WINDOW_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/165
- evidence: `TIMEOUT_BOTTLENECK_CONFIDENCE_WINDOW_REPORT.md` aggregates BL-080/081/083/084/085 windows into `runtime_archives/bl086/tmp/bl086_timeout_bottleneck_summary.tsv` and `bl086_timeout_bottleneck_metrics.json`; measured timeout concentration is `9/11` failed rows (`81.82%`) with terminal JSON-invalid `0/14`, so contract guidance now prioritizes timeout-path mitigation while keeping baseline budgets unchanged
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-087
- title: Run governed timeout failover drill with fallback endpoint profile and rollback criteria
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-086
- start_when: BL-086 confirms timeout remains dominant and runtime contract prioritizes timeout-path mitigation
- done_when: A governed failover drill validates timeout recovery behavior using fallback endpoint configuration, with activation/rollback criteria and archived execute/runtime/state evidence
- source: `TIMEOUT_BOTTLENECK_CONFIDENCE_WINDOW_REPORT.md` on 2026-03-26 shows timeout share among failures `81.82%`, indicating next mitigation should test timeout failover path under governance
- link: /Users/lingguozhong/openclaw-team/TIMEOUT_FAILOVER_DRILL_RUNBOOK_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/167
- evidence: `TIMEOUT_FAILOVER_DRILL_RUNBOOK_REPORT.md` archives BL-087 drill evidence under `runtime_archives/bl087/`; runtime logs confirm `http_524` primary failures followed by retry to fallback endpoint for both automation and critic, request traces record `primary_hits=2` and `fallback_hits=2`, and execute outcome is `processed=1` with `critic_verdict=pass`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-088
- title: Validate timeout failover behavior in production-like provider profile window
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-087
- start_when: BL-087 controlled drill confirms fallback path mechanics work under governed synthetic timeout conditions
- done_when: A short production-like governed window validates timeout failover behavior with real provider profile controls and archives evidence that separates endpoint/network failures from prompt/schema path outcomes
- source: `TIMEOUT_FAILOVER_DRILL_RUNBOOK_REPORT.md` on 2026-03-26 validates failover mechanics in controlled mode, but production-like confidence still requires real profile window evidence
- link: /Users/lingguozhong/openclaw-team/TIMEOUT_FAILOVER_PRODUCTIONLIKE_WINDOW_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/169
- evidence: `TIMEOUT_FAILOVER_PRODUCTIONLIKE_WINDOW_REPORT.md` archives a provider-profile-governed failover window in `runtime_archives/bl088/`; profile snapshot `tmp/provider_profiles.bl088.json` drives primary and fallback routing, runtime logs show `http_524` primary failures followed by fallback retries for both automation and critic, request traces record `primary_hits=2` and `fallback_hits=2`, and execute outcome is `processed=1` with `critic_verdict=pass`
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-089
- title: Quantify fallback success stability across short multi-run production-like timeout windows
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-088
- start_when: BL-088 confirms one production-like provider-profile failover window can recover from primary timeout to fallback success
- done_when: A short multi-run production-like matrix quantifies fallback recovery stability (success rate, verdict quality, wall-time spread) and defines when failover should be considered reliable enough for baseline operational playbooks
- source: `TIMEOUT_FAILOVER_PRODUCTIONLIKE_WINDOW_REPORT.md` on 2026-03-26 validates single-run profile failover behavior but does not yet quantify short-window stability variance
- link: /Users/lingguozhong/openclaw-team/TIMEOUT_FAILOVER_STABILITY_WINDOW_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/171
- evidence: `TIMEOUT_FAILOVER_STABILITY_WINDOW_REPORT.md` archives 4-run matrix evidence in `runtime_archives/bl089/tmp/bl089_profile_failover_stability_matrix.tsv`; outcomes are `processed=4/4`, `critic_verdict=pass` in all runs, complete failover signals in all runs (`http_524 -> fallback` with primary/fallback hits present), and stable wall-time spread (`automation 1.335s-1.400s`, `critic 1.314s-1.349s`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-090
- title: Validate failover stability against mixed transient classes and fallback degradation scenarios
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-089
- start_when: BL-089 confirms short-window failover stability under uniform `http_524` primary-failure pattern
- done_when: A governed mixed-scenario matrix (including `timeout/http_524/http_502` and at least one fallback degradation case) quantifies boundary behavior and defines clear rollback triggers for operational failover playbooks
- source: `TIMEOUT_FAILOVER_STABILITY_WINDOW_REPORT.md` on 2026-03-26 shows strong stability for one transient class pattern, but mixed-class and degraded-fallback boundaries are not yet quantified
- link: /Users/lingguozhong/openclaw-team/MIXED_TRANSIENT_FAILOVER_BOUNDARY_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/173
- evidence: `MIXED_TRANSIENT_FAILOVER_BOUNDARY_REPORT.md` archives BL-090 matrix evidence in `runtime_archives/bl090/tmp/bl090_mixed_failover_boundary_matrix.tsv`; observed automation error classes cover `http_524/http_502/timeout`, success cases (`s01/s02/s03`) recover via fallback with `processed/pass`, and degraded fallback case (`s04`) fails closed (`rejected=1`) with terminal fallback `class=http_502`, establishing explicit rollback triggers
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-091
- title: Run canary-style real endpoint failover observation window with strict rollback guardrails
- type: blocker
- status: done
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-090
- start_when: BL-090 mixed synthetic boundary matrix confirms expected failover and fail-closed behavior across transient classes and degraded fallback scenarios
- done_when: A short canary observation window against real endpoint topology validates failover markers and rollback conditions without changing baseline defaults, with full execute/runtime/state evidence and explicit abort criteria
- source: `MIXED_TRANSIENT_FAILOVER_BOUNDARY_REPORT.md` on 2026-03-26 quantifies synthetic boundaries; next confidence step is canary-style real-topology observation under strict safety guardrails
- link: /Users/lingguozhong/openclaw-team/CANARY_REAL_ENDPOINT_FAILOVER_OBSERVATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/175
- evidence: `CANARY_REAL_ENDPOINT_FAILOVER_OBSERVATION_REPORT.md` archives BL-091 real-topology canary evidence in `runtime_archives/bl091/`; probe matrix shows primary `aixj.vip` path returns `502` while fallback `fast.vpsairobot.com` path returns `401`, observation window `s01..s04` records failover markers (`next_endpoint=https://fast.vpsairobot.com/...`) with terminal rejections (`processed=0/4`, `pass_verdict_rate=0.0`), and rollback guardrails are explicitly triggered (`terminal_rejection_present`, `processed_rate_below_0.75`, `pass_verdict_rate_below_0.75`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-092
- title: Restore fallback credential/profile availability and rerun canary failover window to clear rollback trigger
- type: blocker
- status: blocked
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-091
- start_when: BL-091 canary against real endpoint topology triggers rollback due fallback authorization unavailability and zero processed/pass rates
- done_when: Fallback credential/profile alignment is verified by preflight probe (`200`) and a rerun canary observation window reaches at least `processed_rate >= 0.75` and `pass_verdict_rate >= 0.75` without violating rollback guardrails
- source: `CANARY_REAL_ENDPOINT_FAILOVER_OBSERVATION_REPORT.md` on 2026-03-26 records fallback path `http_401` and mandatory rollback; next blocker is alignment/remediation plus governed rerun
- link: /Users/lingguozhong/openclaw-team/CANARY_FALLBACK_CREDENTIAL_ALIGNMENT_RERUN_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/177
- evidence: `CANARY_FALLBACK_CREDENTIAL_ALIGNMENT_RERUN_REPORT.md` plus `runtime_archives/bl092/tmp/bl092_probe_matrix.tsv` confirm fallback credential/profile preflight availability (`200`) while canary rerun matrix/metrics (`bl092_canary_rerun_matrix.tsv`, `bl092_canary_rerun_metrics.json`) record `processed=1/4`, `pass_verdict_rate=0.25`, mixed `workspace_missing_repo/http_502`, and rollback guardrail triggers
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-093
- title: Stabilize real-endpoint canary rerun by eliminating workspace-mount drift and recovering failover success rate
- type: blocker
- status: blocked
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-092
- start_when: BL-092 rerun confirms fallback credential/profile availability but still fails rollout thresholds due mixed `workspace_missing_repo` and primary `http_502` terminal failures
- done_when: Root cause and mitigation for workspace-mount/runtime inconsistency are evidenced, and a governed 4-sample real-endpoint rerun reaches `processed_rate >= 0.75` and `pass_verdict_rate >= 0.75` without rollback trigger
- source: `CANARY_FALLBACK_CREDENTIAL_ALIGNMENT_RERUN_REPORT.md` on 2026-03-26 shows fallback auth recovery but canary promotion remains blocked by residual runtime instability
- link: /Users/lingguozhong/openclaw-team/CANARY_WORKSPACE_RETRY_STABILIZATION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/178
- evidence: `CANARY_WORKSPACE_RETRY_STABILIZATION_REPORT.md` and `runtime_archives/bl093/tmp/bl093_canary_window_metrics.json` capture BL-093 guarded rerun (`processed=0/4`, `pass_verdict_rate=0.0`) with complete failover markers but terminal endpoint-chain failure class `http_502`; workspace-presence retry hardening landed with unit coverage, yet rollback guardrails remain triggered
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-094
- title: Recover real-endpoint canary success under persistent primary 502 and fallback timeout chain
- type: blocker
- status: blocked
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-093
- start_when: BL-093 confirms workspace-retry hardening but rerun window still fails threshold entirely on endpoint-chain instability (`http_502` + fallback timeout)
- done_when: A governed 4-sample real-endpoint window reaches `processed_rate >= 0.75` and `pass_verdict_rate >= 0.75` with rollback guardrails not triggered, and evidence clearly attributes residual failures by endpoint class
- source: `CANARY_WORKSPACE_RETRY_STABILIZATION_REPORT.md` on 2026-03-26 shows workspace drift not reproduced but canary still fully blocked by endpoint-chain failures
- link: /Users/lingguozhong/openclaw-team/CANARY_ENDPOINT_CHAIN_RECOVERY_PROMPT_COMPACTION_REPORT.md
- issue: https://github.com/Oscarling/openclaw-team/issues/180
- evidence: `CANARY_ENDPOINT_CHAIN_RECOVERY_PROMPT_COMPACTION_REPORT.md` and `runtime_archives/bl094/tmp/bl094_canary_observation_metrics.json` capture BL-094 controlled prompt-compaction rerun (`ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS=1200`) with prompt size reduction but unchanged canary outcome (`processed=0/4`, `pass_verdict_rate=0.0`), complete failover signal `4/4`, and endpoint-chain terminal classes (`http_502`/`remote_closed`) that continue to trigger rollback guardrails
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-095
- title: Recover fallback endpoint stability after BL-094 by isolating remote-closed path under governed canary guardrails
- type: blocker
- status: blocked
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-094
- start_when: BL-094 confirms prompt compaction is active but 4-sample rerun still fails entirely on endpoint-chain instability (`http_502` + fallback `remote_closed/timeout`)
- done_when: A governed 4-sample real-endpoint window reaches `processed_rate >= 0.75` and `pass_verdict_rate >= 0.75` with rollback guardrails not triggered, and evidence proves fallback path no longer degrades to `remote_closed/timeout` under selected provider/endpoint controls
- source: `CANARY_ENDPOINT_CHAIN_RECOVERY_PROMPT_COMPACTION_REPORT.md` on 2026-03-26 records that prompt-size mitigation does not clear endpoint-chain blocker
- link: /Users/lingguozhong/openclaw-team/ENDPOINT_CHAIN_ROUTE_DISCOVERY_PROBE_REPORT.md
- issue: -
- evidence: `ENDPOINT_CHAIN_ROUTE_DISCOVERY_PROBE_REPORT.md` with `runtime_archives/bl095/tmp/bl095_probe_matrix.tsv`, `bl095_payload_sweep.tsv`, `bl095_prompt_limit_probe.tsv`, and `bl095_limit1200_repeats.tsv` shows primary route remains fixed `http_502`, fallback simple probes are `200`, but real automation prompt shape still times out under 45s budget across tested compaction limits (including 4/4 timeout retest at `field_limit=1200`)
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-096
- title: Establish a stable provider/endpoint route for real automation prompt execution before canary clearance
- type: blocker
- status: blocked
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-095
- start_when: BL-095 confirms current provider topology has no stable route for real automation prompt shape despite endpoint/model/compaction probes
- done_when: A candidate provider/endpoint route is validated with repeatable real-automation prompt success and then confirmed by governed 4-sample canary meeting `processed_rate >= 0.75` and `pass_verdict_rate >= 0.75` without rollback trigger
- source: `ENDPOINT_CHAIN_ROUTE_DISCOVERY_PROBE_REPORT.md` on 2026-03-26 records shape-dependent timeout saturation on current fallback route and persistent primary `http_502`
- link: /Users/lingguozhong/openclaw-team/FALLBACK_ONLY_ROUTE_VALIDATION_REPORT.md
- issue: -
- evidence: `FALLBACK_ONLY_ROUTE_VALIDATION_REPORT.md` and `runtime_archives/bl096/tmp/bl096_execute_s01.gpt-5-codex.json` show fallback-only candidate route (`https://fast.vpsairobot.com/v1` + fallback `/responses`) still ends `rejected` with endpoint-chain failure sequence (`timeout -> http_502 -> tls_eof`), so stable promotion path remains unavailable
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-097
- title: Recover canary promotion by introducing an alternative provider route after BL-096 fallback-only rejection
- type: blocker
- status: blocked
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-096
- start_when: BL-096 confirms both mixed-route and fallback-only route still fail governed replay on endpoint-chain instability
- done_when: A new provider/endpoint route is validated through controlled replay and then passes governed 4-sample canary thresholds (`processed_rate >= 0.75`, `pass_verdict_rate >= 0.75`) without rollback trigger
- source: `FALLBACK_ONLY_ROUTE_VALIDATION_REPORT.md` on 2026-03-26 records fallback-only rejection under real replay
- link: /Users/lingguozhong/openclaw-team/ALTERNATIVE_MODEL_GPT54_ROUTE_PROBE_REPORT.md
- issue: -
- evidence: `ALTERNATIVE_MODEL_GPT54_ROUTE_PROBE_REPORT.md` and `runtime_archives/bl097/tmp/bl097_prompt_limit_probe_gpt54.tsv` show that although `gpt-5.4` ping probes return `200`, real automation prompt-shape probes still fail across all tested compaction limits on both fast endpoints (`timeout`/`tls_eof`), so no stable route was recovered
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-098
- title: Provision a new provider/base route for governed replay after BL-097 model-switch failure
- type: blocker
- status: blocked
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-097
- start_when: BL-097 confirms alternative model switch (`gpt-5.4`) does not recover real prompt-shape stability on existing fast endpoints
- done_when: A newly provisioned provider/base route (new key/base topology) passes controlled replay and then governed 4-sample canary thresholds without rollback trigger
- source: `ALTERNATIVE_MODEL_GPT54_ROUTE_PROBE_REPORT.md` on 2026-03-26 records full failure of real prompt-shape probes on existing route
- link: /Users/lingguozhong/openclaw-team/TIMEOUT_BUDGET_GATEWAY_CEILING_PROBE_REPORT.md
- issue: -
- evidence: `TIMEOUT_BUDGET_GATEWAY_CEILING_PROBE_REPORT.md` and `runtime_archives/bl098/tmp/bl098_timeout_budget_probe.tsv` show that increasing timeout budget on the current fast route (`120/180/240/300`) does not recover real automation prompt execution; `120s` ends in timeout and `180/240/300` all terminate at ~126s with `http_524`, indicating an upstream ceiling under current provider/base topology
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260326-099
- title: Onboard a new provider/base topology and clear route handshake gate before replay
- type: blocker
- status: blocked
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-098
- start_when: BL-098 confirms timeout budget tuning (`120/180/240/300`) cannot bypass the current fast-route gateway ceiling (`http_524` near ~126s)
- done_when: A newly supplied provider/base route (new key/base topology) passes lightweight ping and real prompt-shape probe, then is promoted into controlled replay validation
- source: `PROVIDER_HANDSHAKE_ASSESSMENT_AUTOMATION_REPORT.md` on 2026-03-28 confirms retest matrix remains blocked and classifies dominant cause as auth/access policy block
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ROUTE_RETEST_20260327_REPORT.md
- issue: -
- evidence: `PROVIDER_ONBOARDING_INPUT_BLOCK_REPORT.md`, `PROVIDER_ROUTE_RETEST_20260327_REPORT.md`, `PROVIDER_HANDSHAKE_ASSESSMENT_AUTOMATION_REPORT.md`, `PROVIDER_ONBOARDING_GATE_WRAPPER_REPORT.md`, `PROVIDER_ONBOARDING_HISTORY_SUMMARY_AUTOMATION_REPORT.md`, `PROVIDER_ONBOARDING_GATE_SUMMARY_REFRESH_REPORT.md`, `PROVIDER_ONBOARDING_HISTORY_REPO_FILTER_HARDENING_REPORT.md`, `PROVIDER_ONBOARDING_HISTORY_VALIDATION_HARDENING_REPORT.md`, `PROVIDER_ONBOARDING_HISTORY_CONSISTENCY_HARDENING_REPORT.md`, `PROVIDER_ONBOARDING_NOTE_SIGNAL_HISTORY_HARDENING_REPORT.md`, `PROVIDER_ONBOARDING_NOTE_SIGNAL_COVERAGE_METRICS_REPORT.md`, `runtime_archives/bl099/tmp/bl099_key3_probe_matrix.tsv`, `runtime_archives/bl100/tmp/provider_handshake_probe_retest_allkeys_20260327b.tsv`, `runtime_archives/bl100/tmp/provider_handshake_assessment_20260328.json`, `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv`, `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json`, `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` show all currently known Desktop key candidates still fail handshake (`aixj=401 INVALID_API_KEY`, `fast=403/1010` with occasional transport/TLS `000`) and no `2xx` route is available for controlled replay
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-26

### BL-20260326-100
- title: Productize local probe script and no-key wait-mode hardening while BL-099 is blocked
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-099
- start_when: BL-099 is blocked due unavailable authenticated provider/base+key route
- done_when: A repo-tracked probe script/runbook replaces ad-hoc `/tmp` probing and produces reproducible handshake evidence without exposing secrets
- source: `PROVIDER_ONBOARDING_INPUT_BLOCK_REPORT.md` on 2026-03-26 records current input-side block
- link: /Users/lingguozhong/openclaw-team/WAIT_MODE_PROBE_SCRIPT_PRODUCTIZATION_REPORT.md
- issue: -
- evidence: `scripts/provider_handshake_probe.py` and validation matrices `runtime_archives/bl100/tmp/provider_handshake_probe_missing_key.tsv` + `runtime_archives/bl100/tmp/provider_handshake_probe_key3.tsv` prove the no-key wait-mode handshake probe is now reproducible in-repo with key-tail masking and deterministic TSV output
- last_reviewed_at: 2026-03-26
- opened_at: 2026-03-26

### BL-20260327-101
- title: Add handshake success gate and unit coverage for provider probe script
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260326-100
- start_when: BL-100 has landed the repo-tracked probe script and BL-099 remains blocked on provider onboarding
- done_when: Probe script supports explicit success gating (`--require-success`) and dedicated unit tests cover key extraction, masking, missing-key, and success/failure exit behavior
- source: `PROVIDER_ROUTE_RETEST_20260327_REPORT.md` confirms provider onboarding remains blocked and requires deterministic fail-fast gating
- link: /Users/lingguozhong/openclaw-team/PROBE_GATE_REQUIRE_SUCCESS_HARDENING_REPORT.md
- issue: -
- evidence: `PROBE_GATE_REQUIRE_SUCCESS_HARDENING_REPORT.md`, `scripts/provider_handshake_probe.py`, `tests/test_provider_handshake_probe.py`, and `runtime_archives/bl100/tmp/provider_handshake_probe_gatecheck_20260327.tsv` verify explicit `--require-success` gating with passing unit coverage and live non-2xx fail-fast behavior (exit code `2`)
- last_reviewed_at: 2026-03-27
- opened_at: 2026-03-27

### BL-20260328-102
- title: Automate handshake probe assessment and blocked-cause classification
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260327-101
- start_when: Probe execution and success-gating are in place but matrix interpretation is still manual
- done_when: A repo script consumes handshake TSV, emits structured readiness summary, supports fail-fast `--require-ready`, and is covered by dedicated unit tests integrated in premerge checks
- source: `PROVIDER_ROUTE_RETEST_20260327_REPORT.md` on 2026-03-27 leaves BL-099 blocked and motivates deterministic post-probe classification
- link: /Users/lingguozhong/openclaw-team/PROVIDER_HANDSHAKE_ASSESSMENT_AUTOMATION_REPORT.md
- issue: -
- evidence: `scripts/provider_handshake_assess.py`, `tests/test_provider_handshake_assess.py`, `scripts/premerge_check.sh`, and `runtime_archives/bl100/tmp/provider_handshake_assessment_20260328.json` provide automated `ready/blocked` assessment with explicit `block_reason` and fail-fast exit semantics
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-103
- title: Add one-shot provider onboarding gate wrapper for local fail-fast execution
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-102
- start_when: Probe and assessment scripts are available but still run as separate manual commands
- done_when: A single wrapper command executes `probe -> assess`, preserves `--require-ready` exit semantics, and is covered by tests integrated into premerge checks
- source: `PROVIDER_HANDSHAKE_ASSESSMENT_AUTOMATION_REPORT.md` on 2026-03-28 motivates reducing manual command orchestration while BL-099 remains blocked
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_GATE_WRAPPER_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_gate.py`, `tests/test_provider_onboarding_gate.py`, `scripts/premerge_check.sh`, `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv`, and `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json` provide one-shot gating with expected blocked fail-fast behavior (exit code `2`)
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-104
- title: Persist onboarding gate run history and keep test runs noise-free
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-103
- start_when: One-shot gate wrapper is available but outcome history is not yet persisted for cross-session auditing
- done_when: Gate wrapper appends run metadata to JSONL history, tests avoid writing noise via `--no-history`, and one real run history entry is archived
- source: `PROVIDER_ONBOARDING_GATE_WRAPPER_REPORT.md` on 2026-03-28 establishes wrapper baseline and motivates persistent run tracking
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_GATE_HISTORY_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_gate.py`, `tests/test_provider_onboarding_gate.py`, `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`, `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv`, and `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json` confirm history persistence with blocked status metadata and noise-free test behavior
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-105
- title: Publish local provider onboarding runbook for probe/assess/gate operations
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-104
- start_when: Probe/assessment/gate scripts are available but command usage is still memory-dependent
- done_when: A repo-tracked runbook documents command paths, fail-fast options, outputs, and decision rules for local-first onboarding
- source: local hardening continuation after gate tooling productization
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md
- issue: -
- evidence: `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md` documents handshake probe, assessment, and one-shot gate commands with fail-fast semantics and output conventions
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-106
- title: Refine handshake assessment with note-level signal classification
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-105
- start_when: Assessment script provides code-level readiness but lacks structured note-level signal breakdown
- done_when: Assessment script emits note-class counts and distinguishes mixed transport causes (TLS/DNS) with dedicated tests and refreshed assessment output
- source: local hardening continuation to improve blocked-cause precision under BL-099
- link: /Users/lingguozhong/openclaw-team/PROVIDER_HANDSHAKE_NOTE_CLASSIFICATION_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_handshake_assess.py`, `tests/test_provider_handshake_assess.py`, and `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json` provide note-level signal classification (`note_class_counts`) and refined block reason selection
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-107
- title: Automate onboarding history trend summary generation
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-106
- start_when: Gate history JSONL exists but trend interpretation still requires manual reading
- done_when: A repo script generates summary JSON with counts and latest snapshot, with dedicated tests integrated into premerge checks
- source: local hardening continuation after onboarding gate history persistence
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_HISTORY_SUMMARY_AUTOMATION_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_history_summary.py`, `tests/test_provider_onboarding_history_summary.py`, `scripts/premerge_check.sh`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary_20260328.json` provide automated trend summary generation from onboarding gate history
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-108
- title: Auto-refresh onboarding history summary in one-shot gate
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-107
- start_when: Gate writes history JSONL but summary refresh still depends on manual command execution
- done_when: Gate refreshes history summary JSON automatically after each persisted run and exposes an explicit opt-out switch for controlled tests
- source: local hardening continuation to keep onboarding status snapshots synchronized by default
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_GATE_SUMMARY_REFRESH_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_gate.py`, `tests/test_provider_onboarding_gate.py`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` confirm automatic summary refresh and opt-out behavior (`--no-history-summary`)
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-109
- title: Harden onboarding history summary with repo-path filtering
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-108
- start_when: Gate summary can be polluted by non-repo temporary history entries from ad-hoc/test runs
- done_when: Summary supports repo-only filtering with explicit dropped counter, gate defaults to repo-only refresh, and tests cover default + opt-out behavior
- source: local hardening continuation to keep blocker trend metrics stable and noise-resistant
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_HISTORY_REPO_FILTER_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_history_summary.py`, `scripts/provider_onboarding_gate.py`, `tests/test_provider_onboarding_history_summary.py`, `tests/test_provider_onboarding_gate.py`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` confirm repo-only summary filtering and explicit opt-out (`--no-history-summary-repo-only`)
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-110
- title: Enforce onboarding history JSONL schema/path integrity in premerge
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-109
- start_when: History aggregation is hardened, but no dedicated fail-closed schema/path validator guards JSONL integrity before merge
- done_when: Dedicated history validation script and tests exist, premerge gate runs both tests and real-history validation with repo-path enforcement
- source: local hardening continuation to keep blocker evidence deterministic and merge-safe
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_HISTORY_VALIDATION_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_history_validate.py`, `tests/test_provider_onboarding_history_validate.py`, `scripts/premerge_check.sh`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl` confirm fail-closed validation for history schema and repo-path integrity
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-111
- title: Enforce onboarding history-summary consistency in premerge
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-110
- start_when: History schema/path checks exist, but stale summary JSON can still diverge from history without explicit consistency gate
- done_when: Dedicated consistency checker and tests exist, and premerge fails when summary JSON mismatches recomputed history summary under repo-only rules
- source: local hardening continuation to prevent stale summary snapshots from entering blocker evidence
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_HISTORY_CONSISTENCY_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_history_consistency_check.py`, `tests/test_provider_onboarding_history_consistency_check.py`, `scripts/premerge_check.sh`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` confirm fail-closed history-summary consistency checks
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-112
- title: Persist and summarize note-level handshake signals in onboarding history
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-111
- start_when: Summary/governance pipeline is stable but note-level diagnostics are not consistently carried through history snapshots
- done_when: Gate writes `note_class_counts` into history entries, summary aggregates note-level counters, validators enforce shape, and consistency checks include note-level field
- source: local hardening continuation to improve signal-level trend visibility while BL-099 remains blocked
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_NOTE_SIGNAL_HISTORY_HARDENING_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_gate.py`, `scripts/provider_onboarding_history_summary.py`, `scripts/provider_onboarding_history_validate.py`, `scripts/provider_onboarding_history_consistency_check.py`, `tests/test_provider_onboarding_gate.py`, `tests/test_provider_onboarding_history_summary.py`, `tests/test_provider_onboarding_history_validate.py`, `tests/test_provider_onboarding_history_consistency_check.py`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` confirm note-level signal continuity across history, summary, and premerge checks
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28

### BL-20260328-113
- title: Add note-signal coverage metrics to onboarding history summary
- type: debt
- status: done
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260328-112
- start_when: Note-level counters are persisted, but summary lacks explicit completeness metrics for historical rows missing signal payloads
- done_when: Summary exposes note-signal coverage metrics, consistency check validates them, tests cover coverage behavior, and runbook documents metric interpretation
- source: local hardening continuation to make note-signal completeness measurable while BL-099 remains blocked
- link: /Users/lingguozhong/openclaw-team/PROVIDER_ONBOARDING_NOTE_SIGNAL_COVERAGE_METRICS_REPORT.md
- issue: -
- evidence: `scripts/provider_onboarding_history_summary.py`, `scripts/provider_onboarding_history_consistency_check.py`, `tests/test_provider_onboarding_history_summary.py`, `tests/test_provider_onboarding_history_consistency_check.py`, `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`, and `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json` confirm coverage metrics (`rows_with_note_class_counts`, `rows_missing_note_class_counts`, `note_signal_coverage_percent`) are generated and consistency-checked
- last_reviewed_at: 2026-03-28
- opened_at: 2026-03-28
