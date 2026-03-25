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
- status: planned
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260325-033
- start_when: `BL-20260325-033` has completed and confirmed the main runtime rejection shifted to critic-side truncated wrapper snapshot evidence rather than explicit report-flag mismatch
- done_when: Critic evidence handoff preserves complete wrapper artifact content (or equivalent complete review context) for generated script reviews, focused tests cover snapshot-size/completeness behavior, and one phase report records the hardening outcome
- source: `POST_REPORT_FLAG_REALIGNMENT_VALIDATION_REPORT.md` on 2026-03-25 records that fresh governed validation still returns `needs_revision` due critic-side truncated wrapper snapshot evidence
- link: /Users/lingguozhong/openclaw-team/CRITIC_SNAPSHOT_COMPLETENESS_HARDENING_REPORT.md
- issue: deferred:phase=next until BL-20260325-033 lands on main
- evidence: -
- last_reviewed_at: 2026-03-25
- opened_at: 2026-03-25
