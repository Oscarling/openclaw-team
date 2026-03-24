# Trello Readonly Ingress Hardening Report

## Scope

This report covers a narrow hardening pass on the Trello read-only entry path:

- [skills/trello_readonly_prep.py](/Users/lingguozhong/openclaw-team/skills/trello_readonly_prep.py)
- [skills/ingest_tasks.py](/Users/lingguozhong/openclaw-team/skills/ingest_tasks.py)

The goal was not to expand the control chain. The goal was to make the Trello
read-only path safer to validate and maintain by removing the hard import-time
dependency on `requests`, adding dedicated unit coverage, and wiring that
coverage into the normal premerge / CI gates.

## Implemented

- `skills/trello_readonly_prep.py` now tolerates a missing `requests` install at
  import time and accepts an injected `requests_get` callable for tests.
- `skills/ingest_tasks.py` now uses the same dependency-safe pattern for the
  Trello read-only HTTP entry point.
- Added
  [tests/test_trello_readonly_ingress.py](/Users/lingguozhong/openclaw-team/tests/test_trello_readonly_ingress.py)
  to cover:
  - missing credentials blocking before HTTP
  - successful read-only smoke with mapped preview output
  - forbidden board access classification
  - inbox payload creation from Trello cards
  - missing `requests` dependency surfacing as a clear runtime error
  - HTTP error preview propagation
- Added the new test file to:
  - [scripts/premerge_check.sh](/Users/lingguozhong/openclaw-team/scripts/premerge_check.sh)
  - [.github/workflows/ci.yml](/Users/lingguozhong/openclaw-team/.github/workflows/ci.yml)
- Updated
  [docs/ENGINEERING_WORKFLOW.md](/Users/lingguozhong/openclaw-team/docs/ENGINEERING_WORKFLOW.md)
  so the enforced baseline matches the repo's real test gate.

## Validation

Commands run locally:

```bash
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
python3 -m unittest -v tests/test_trello_readonly_ingress.py
python3 -m unittest -v tests/test_processed_finalization.py tests/test_pin_trello_done_list.py
```

Observed result:

- all commands passed
- the new Trello read-only ingress tests passed `6/6`
- existing finalization and Done-list pinning tests remained green

## Non-Goals

- no real Trello smoke run was added in this pass
- no execute / approval semantics changed
- no finalization / Trello writeback behavior changed

## Remaining Gaps

- real Trello read-only connectivity still depends on valid runtime credentials
  and scope ids
- this pass hardens testability and guardrails, but it does not itself prove live
  Trello availability on the target runtime
