# PREVIEW_REGENERATION_PATH_REPORT

## Objective

Add one explicit, governed way to regenerate a preview for the same `origin_id`
without weakening the default Trello read-only preview freeze.

This phase exists because:

- `BL-20260324-018` hardened the source-side preview contract
- `BL-20260324-019` needs a fresh preview candidate to validate that hardening
- the current freeze intentionally blocks a simple same-origin re-preview
- the user explicitly chose a regeneration-path phase over a fresh-card path

## Scope

In scope:

- local inbox payload validation
- same-origin dedupe semantics at ingest time
- preview and ingest sidecar audit visibility
- regression coverage for the new governed behavior

Out of scope:

- changing `skills/execute_approved_previews.py`
- reinterpreting `--allow-replay` as regeneration
- automatic content-change re-entry for the same Trello card
- Git finalization or Trello writeback

## Implemented Design

The minimal-safe path is an explicit `regeneration_token`.

Rules now implemented:

- default behavior is unchanged:
  same-origin preview creation still dedupes on `origin:<origin_id>`
- regeneration is opt-in only:
  a caller must provide `regeneration_token`
- regeneration requires an explicit `origin_id`
- if `regeneration_token` is repeated across top-level payload, `metadata`, or
  `source`, the values must match
- a regeneration request uses dedupe key
  `origin_regeneration:<origin_id>:<token>` instead of `origin:<origin_id>`
- the token is copied into preview evidence and ingest sidecars so the new
  preview is audit-visible rather than a silent dedupe bypass

This keeps replay protection and the default freeze intact while allowing one
controlled new preview per explicit token.

## Files Changed

- `PROJECT_BACKLOG.md`
- `BASELINE_FREEZE_NOTE.md`
- `adapters/local_inbox_adapter.py`
- `skills/ingest_tasks.py`
- `tests/test_local_inbox_adapter.py`
- `tests/test_trello_readonly_ingress.py`

## Verification

Phase-local smoke + regressions on 2026-03-24:

```bash
python3 -m unittest -v \
  tests.test_trello_readonly_ingress.TrelloReadonlyIngressTests.test_process_one_allows_controlled_regeneration_and_blocks_token_reuse \
  tests.test_trello_readonly_ingress.TrelloReadonlyIngressTests.test_process_one_blocks_same_origin_duplicate_without_regeneration_token \
  tests.test_local_inbox_adapter.LocalInboxAdapterTests.test_normalize_local_inbox_payload_uses_explicit_regeneration_token_for_dedupe \
  tests.test_local_inbox_adapter.LocalInboxAdapterTests.test_validate_external_payload_rejects_regeneration_without_explicit_origin
```

Result:

- `4/4` passed
- smoke proved the same origin can create a new preview when an explicit token is
  present and that reusing the same token is still blocked
- regressions proved the default same-origin freeze still blocks duplicate
  preview creation and that regeneration cannot be requested without an explicit
  `origin_id`

Broader focused suites on 2026-03-24:

```bash
python3 -m unittest tests.test_local_inbox_adapter
python3 -m unittest tests.test_trello_readonly_ingress
```

Result:

- `tests.test_local_inbox_adapter`: `4/4` passed
- `tests.test_trello_readonly_ingress`: `10/10` passed
- `python3 scripts/backlog_lint.py` passed
- `python3 scripts/backlog_sync.py` passed while `BL-20260324-020` was mirrored
  to issue `#31`, and passed again after closeout with no remaining `phase=now`
  actionable items requiring mirroring
- `bash scripts/premerge_check.sh` passed with `Warnings: 0` and `Failures: 0`

## Gstack Checkpoint Note

`plan-eng-review` was not separately run for this phase.

Reason:

- the change is deliberately constrained to the ingest contract
- `BASELINE_FREEZE_NOTE.md` already narrowed the allowed direction to an explicit
  rerun/replay token style re-entry
- no executor, approval, or finalization architecture was changed

The next phase, `BL-20260324-019`, remains the governed validation phase for the
new regenerated preview candidate.
