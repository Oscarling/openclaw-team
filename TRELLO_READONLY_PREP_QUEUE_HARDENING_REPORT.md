# Trello Readonly Prep Queue Hardening Report

## Scope

This report covers the follow-up hardening for the queue pollution discovered in
[TRELLO_READONLY_PREVIEW_SMOKE_REPORT.md](/Users/lingguozhong/openclaw-team/TRELLO_READONLY_PREVIEW_SMOKE_REPORT.md).

Problem:

- `skills/trello_readonly_prep.py --smoke-read` wrote a fixture-mapped sample to
  `processing/trello_readonly_mapped_sample.json`
- the next real ingest run recovered that file as live queue input
- this created an extra duplicate result unrelated to the live Trello fetch

Goal:

- keep the prep helper useful
- keep its default output outside the live processing queue
- prove the fix with tests and one rerun of the governed Trello preview smoke

## Gstack Checkpoint Decision

Explicit skip rationale:

- no extra gstack checkpoint was used for this phase because the change is a
  narrow helper-output-path fix with no architecture expansion, no trust-boundary
  change, and no new live write behavior
- standard local verification plus the governed rerun smoke were sufficient for
  this scope

## Implemented

- changed the default mapped output path in
  [skills/trello_readonly_prep.py](/Users/lingguozhong/openclaw-team/skills/trello_readonly_prep.py)
  from `processing/trello_readonly_mapped_sample.json` to:
  `artifacts/trello_readonly_prep/trello_readonly_mapped_sample.json`
- added regression coverage in
  [tests/test_trello_readonly_ingress.py](/Users/lingguozhong/openclaw-team/tests/test_trello_readonly_ingress.py)
  to verify:
  - the default prep output path stays outside `processing/`
  - argument parsing uses the safe default path

## Local Verification

Commands run:

```bash
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
python3 -m unittest -v tests/test_trello_readonly_ingress.py
```

Observed result:

- backlog lint passed
- backlog sync passed with `BL-20260324-012 -> #20`
- Trello read-only ingress tests passed `8/8`

## Governed Rerun Smoke

Commands run:

```bash
source /tmp/trello_env.sh && python3 skills/trello_readonly_prep.py --smoke-read --limit 1
source /tmp/trello_env.sh && python3 skills/ingest_tasks.py --once --trello-readonly-once --trello-limit 3
```

Observed result:

- `skills/trello_readonly_prep.py --smoke-read` now reports:
  - `mapped_output = /Users/lingguozhong/openclaw-team/artifacts/trello_readonly_prep/trello_readonly_mapped_sample.json`
- the subsequent governed ingest rerun completed with:
  - `processed = 0`
  - `rejected = 3`
  - `duplicate_skipped = 3`
  - `preview_created = 0`
  - `processing_recovered = 0`

Interpretation:

- the queue-pollution bug is fixed
- the extra duplicate from recovered sample output is gone
- the live Trello cards in scope still hit existing dedupe history, so no new
  preview was created in this rerun either

## Remaining Gap

The next blocker is no longer prep-helper pollution. The remaining blocker is
sample freshness:

- the current live board slice being fetched still maps to cards already present
  in local dedupe history
- the next realistic step is to identify or provide an unseen live Trello card
  or narrower live scope for a clean preview-creation smoke
