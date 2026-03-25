# Critic Snapshot Completeness Hardening Report

## Objective

Complete `BL-20260325-034` by reducing truncation-driven false negatives in
critic review input so wrapper/delegate reviews can evaluate sufficiently
complete artifact context.

## Scope

In scope:

- critic artifact snapshot limit hardening in execute path
- configurable snapshot-size policy with safe bounds
- focused regression coverage for non-truncation and truncation behavior

Out of scope:

- fresh governed live Trello validation run
- prompt-policy redesign for critic semantics
- git finalization / Trello Done writeback

## Changes

### 1) Increased default snapshot limit and made it configurable

Updated `skills/execute_approved_previews.py`:

- replaced fixed `MAX_SNAPSHOT_CHARS = 12000` with resolved policy:
  - `DEFAULT_MAX_SNAPSHOT_CHARS = 120000`
  - env override `ARGUS_CRITIC_MAX_SNAPSHOT_CHARS`
  - bounded to `[4096, 500000]`
- added `_resolve_max_snapshot_chars()` for robust parsing/fallback behavior

This keeps defaults large enough for typical wrapper scripts while preserving
operational guardrails.

### 2) Added focused snapshot-size regressions

Updated `tests/test_execute_approved_previews.py` with:

- `test_build_critic_from_automation_keeps_full_content_under_default_limit`
  - verifies a 15k+ wrapper artifact is no longer truncated under default
    policy
- `test_build_critic_from_automation_truncates_when_limit_exceeded`
  - verifies truncation remains deterministic when limit is explicitly lowered

Existing critic-artifact preservation tests remain intact.

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_execute_approved_previews.py`
- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-034` can be treated as complete as a source-side hardening phase.

The critic snapshot handoff now defaults to materially larger artifact context
with bounded configurability and focused coverage.

Next required step: run a fresh same-origin governed validation to verify
runtime critic outcomes under the updated snapshot policy.
