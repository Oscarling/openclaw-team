# Runtime Residue Archive Note

## Archived Snapshot

- Source preview path: `preview/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.json`
- Archive snapshot: `docs/archive/runtime_residue/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.failed-replay-2026-03-24.json`
- Archived on: `2026-03-24`
- SHA-256: `ca6a752a80f3f7a357599398746594de21da7baad54b59a0497688d6110c07dc`

## What This Captures

This archive preserves the local failed replay mutation created while reusing an
already-finalized preview during formal upstream smoke preparation on
`2026-03-24`.

The archived JSON records:

- `finalization.status = failed`
- `finalization.last_error = "No staged changes found for processed preview"`
- the candidate path set that had already been committed in the earlier smoke

## Why It Was Archived

Leaving this file modified in `preview/` kept the working tree dirty and blocked
future governed smoke / merge gates. The failed replay state was still useful as
audit evidence, so the state was copied here before cleanup.

## Cleanup Action

After archiving this snapshot, the source preview file under `preview/` was
restored to its committed state. The authoritative historical evidence for the
original successful smoke remains in:

- `PROCESSED_FINALIZATION_REPORT.md`
- `approvals/preview-trello-69c1229edc9b8ec895640c5b-d01d1c92df6b.finalization.result.json`

## Follow-on Context

The repository later completed a fresh formal upstream smoke using a new Trello
sample and real `origin` push on branch
`ops/finalization/formal-smoke-20260324`. See:

- `PROCESSED_FINALIZATION_REPORT.md`
- `PROJECT_CHAT_AND_WORK_LOG.md`
