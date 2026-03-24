# Trello Readonly Preview Smoke Report

## Scope

This report covers one governed real Trello read-only smoke after the Trello
ingress hardening work landed on `main`.

Target path:

`Trello read-only -> adapter mapping -> inbox -> preview-only ingest`

Out of scope:

- approval
- execute
- git finalization
- Trello writeback / Done

## Pre-Run Gate

Checked before the real run:

- reviewed
  [PROJECT_CHAT_AND_WORK_LOG.md](/Users/lingguozhong/openclaw-team/PROJECT_CHAT_AND_WORK_LOG.md)
- reviewed
  [BASELINE_FREEZE_NOTE.md](/Users/lingguozhong/openclaw-team/BASELINE_FREEZE_NOTE.md)
- `git status --short` was clean before the run
- runtime directories had no unclassified tracked residue in git status
- `/tmp/trello_env.sh` exposed Trello read-only credentials and board scope
  without needing to reveal secret values
- exact commands were fixed before execution

## Commands Run

```bash
source /tmp/trello_env.sh && python3 skills/trello_readonly_prep.py --smoke-read --limit 1
source /tmp/trello_env.sh && python3 skills/ingest_tasks.py --once --trello-readonly-once --trello-limit 3
```

## Observed Result

### 1. Read-only GET smoke

Result:

- status: `pass`
- scope kind: `board`
- read count: `1`
- auth env selection:
  - key: `TRELLO_API_KEY`
  - token: `TRELLO_API_TOKEN`
- mapped first live card:
  - `origin_id = trello:69c1fff1b3339965c25783b7`
  - `list_id = 69be462743bfa0038ca10f91`

Interpretation:

- live Trello read-only connectivity is currently real and working
- the current runtime env is sufficient for GET-only board access

### 2. Preview-only ingest run

Result summary from `skills/ingest_tasks.py`:

- `processed = 0`
- `rejected = 4`
- `duplicate_skipped = 4`
- `preview_created = 0`
- `inbox_claimed = 3`
- `processing_recovered = 1`

Live Trello cards fetched in this smoke all hit existing dedupe history:

- `trello:69bff951f79026ca5f386743`
- `trello:69c1229edc9b8ec895640c5b`
- `trello:69c1fff1b3339965c25783b7`

Concrete evidence:

- [rejected/trello-readonly-69c1fff1b3339965c25783b7.json.result.json](/Users/lingguozhong/openclaw-team/rejected/trello-readonly-69c1fff1b3339965c25783b7.json.result.json)
  records `decision = duplicate_skipped` with
  `keys=origin:trello:69c1fff1b3339965c25783b7`

Interpretation:

- the real Trello read-only path is live
- this exact smoke did not create a new preview because the fetched live cards
  were already present in local dedupe state
- the no-execute invariant held: no approval or execution path was entered

## Newly Exposed Side Effect

One additional duplicate came from a recovered local sample file rather than from
the live Trello fetch:

- [rejected/trello_readonly_mapped_sample.json.result.json](/Users/lingguozhong/openclaw-team/rejected/trello_readonly_mapped_sample.json.result.json)

What happened:

- `skills/trello_readonly_prep.py --smoke-read` still wrote its fixture-mapped
  sample output to `processing/trello_readonly_mapped_sample.json`
- the subsequent real ingest run recovered that file as live processing input
- that sample then got rejected as another duplicate

This does not invalidate the live Trello result, but it does mean the prep helper
still contaminates the live processing queue during smoke workflows.

## Conclusion

The real read-only Trello integration is currently usable for GET-only access, but
the current board slice surfaced only cards already known to the repo's dedupe
history, so this smoke produced no new preview.

The next follow-up should not guess around that result. It should explicitly fix
the prep-helper queue pollution first, then rerun a clean preview smoke.
