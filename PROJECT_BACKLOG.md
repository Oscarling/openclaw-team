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
- status: active
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: Governance baseline branch is available for follow-up process hardening
- done_when: PROJECT_BACKLOG.md, backlog lint, CI, and merge gates are all merged through normal review
- source: PROJECT_CHAT_AND_WORK_LOG.md
- link: https://github.com/Oscarling/openclaw-team/pull/1
- issue: https://github.com/Oscarling/openclaw-team/issues/3
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-002
- title: Merge formal preview smoke hardening through a reviewed PR
- type: blocker
- status: active
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: -
- start_when: fix/formal-preview-smoke-hardening branch is ready for review
- done_when: The hardening PR merges to main with required checks green
- source: PROCESSED_FINALIZATION_REPORT.md
- link: https://github.com/Oscarling/openclaw-team/pull/2
- issue: https://github.com/Oscarling/openclaw-team/issues/4
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-003
- title: Enable branch protection for main with required CI and review
- type: blocker
- status: planned
- phase: now
- priority: p1
- owner: Oscarling
- depends_on: BL-20260324-001, BL-20260324-002
- start_when: Governance and smoke-hardening PR branches are ready to enter normal merge flow
- done_when: main rejects direct push and requires passing CI plus at least one review
- source: PROJECT_CHAT_AND_WORK_LOG.md
- link: https://github.com/Oscarling/openclaw-team/settings/branches
- issue: https://github.com/Oscarling/openclaw-team/issues/5
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-004
- title: Mirror active backlog items into GitHub issues
- type: sideline
- status: active
- phase: now
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-001
- start_when: The backlog format and lint gate are merged so issue mirroring has a stable source
- done_when: Each phase=now actionable backlog item has a linked GitHub issue and mirror checks run in local gates plus CI
- source: PROJECT_BACKLOG.md
- link: https://github.com/Oscarling/openclaw-team/pull/7
- issue: https://github.com/Oscarling/openclaw-team/issues/6
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24

### BL-20260324-005
- title: Pin TRELLO_DONE_LIST_ID in the formal runtime environment
- type: debt
- status: planned
- phase: next
- priority: p2
- owner: Oscarling
- depends_on: BL-20260324-002
- start_when: The formal preview smoke hardening is merged and the runtime environment is ready for one config pass
- done_when: Formal finalization no longer depends on list-name lookup for the Done list
- source: PROCESSED_FINALIZATION_REPORT.md
- link: /tmp/trello_env.sh
- issue: deferred:after-formal-preview-hardening-merges
- evidence: -
- last_reviewed_at: 2026-03-24
- opened_at: 2026-03-24
