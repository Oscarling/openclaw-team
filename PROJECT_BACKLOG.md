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
- status: planned
- phase: next
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-012
- start_when: Prep-helper queue pollution is fixed and the next blocker is no longer local sample contamination
- done_when: A governed real Trello preview smoke targets an unseen live card or narrower live scope and truthfully records whether a new preview is created
- source: `TRELLO_READONLY_PREP_QUEUE_HARDENING_REPORT.md` on 2026-03-24 confirmed `processing_recovered=0` but the live fetched cards still hit existing dedupe history
- link: /Users/lingguozhong/openclaw-team/TRELLO_READONLY_PREP_QUEUE_HARDENING_REPORT.md
- issue: deferred:promote-when-fresh-live-sample-plan-is-ready
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24
