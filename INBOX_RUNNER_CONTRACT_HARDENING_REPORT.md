# Inbox Runner Contract Hardening Report

## Objective

Resolve the residual runner-level contract gaps exposed by
`BL-20260324-019` before another governed validation round or any production
use of the generated inbox runner.

This phase is intentionally narrow:

- harden the generated runner artifact that was carried forward as evidence
- add focused regression coverage for the new contract points
- keep the branch limited to runner semantics, tests, and merge gates

## Scope

In scope:

- dry-run result semantics
- zero-input short-circuit behavior
- delegate path resolution
- explicit readonly delegate enforcement
- propagation of reviewable `partial` status
- baseline gate updates for the new runner tests

Out of scope:

- another live Trello preview generation
- another approval / execute run
- changes to `artifacts/scripts/pdf_to_excel_ocr.py`
- Git finalization
- Trello writeback / Done

## Findings Addressed

`HARDENED_PREVIEW_VALIDATION_REPORT.md` and the latest critic review surfaced
five runner-level concerns:

1. dry-run returned `status = success` without an `.xlsx` output
2. the runner had no `partial` status for reviewable intermediate outcomes
3. `preferred_base_script` was resolved from `Path.cwd()`
4. readonly behavior was only implied by metadata, not enforced in delegation
5. zero-PDF discovery still flowed into delegation instead of short-circuiting

## Implemented Changes

Files changed:

- `PROJECT_BACKLOG.md`
- `PROJECT_CHAT_AND_WORK_LOG.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/ci.yml`
- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `scripts/premerge_check.sh`
- `tests/test_pdf_to_excel_ocr_inbox_runner.py`

### 1. Reviewable partial outcomes for non-output paths

`artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` now:

- returns `status = partial` for dry-run requests
- returns `status = partial` when zero PDFs are discovered
- exits successfully for `partial` outcomes so the surrounding system can treat
  them as reviewable results instead of hard failures

This removes the old ambiguity where dry-run looked like artifact-production
success.

### 2. Repo-root delegate resolution

The runner now resolves relative delegate paths from the repository root derived
from `__file__`, not from the caller's current working directory.

This makes the runner portable across shells and CI working directories while
keeping the summary evidence explicit about the resolved script path.

### 3. Explicit readonly delegate contract

The runner now records a `contract` section in its summary and enforces that the
delegate resolves to the reviewed repository script
`artifacts/scripts/pdf_to_excel_ocr.py`.

This does not make OCR conversion filesystem-readonly. It does make the Trello
preview contract more explicit by refusing delegation to an arbitrary script that
could silently broaden behavior beyond the reviewed reuse path.

### 4. Partial propagation from delegate evidence

When the reviewed base script emits structured JSON, the runner now parses the
delegate report and preserves `partial` when the delegate produced an `.xlsx`
artifact but reported a reviewable partial outcome.

This aligns the runner with the repo's existing `success` / `partial` / `failed`
status model instead of collapsing everything into `success` or `failed`.

### 5. Focused regression coverage and gate wiring

Added `tests/test_pdf_to_excel_ocr_inbox_runner.py` to lock in:

- dry-run partial semantics
- zero-input partial short-circuiting
- repo-root path resolution
- rejection of unreviewed delegates
- propagation of delegate `partial` status

The new suite is enforced in:

- `scripts/premerge_check.sh`
- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`

## Verification

Commands run on 2026-03-24:

```bash
python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
bash scripts/premerge_check.sh
git diff --check
```

Observed result:

- `tests/test_pdf_to_excel_ocr_inbox_runner.py` passed `5/5`
- `python3 scripts/backlog_lint.py` passed
- `python3 scripts/backlog_sync.py` passed while `BL-20260324-021` was mirrored
  to issue `#35`, and passed again after closeout with no remaining `phase=now`
  actionable items requiring mirroring
- `bash scripts/premerge_check.sh` passed with `Warnings: 0` and `Failures: 0`,
  including the new runner suite plus the existing baseline suites
- `git diff --check` passed with no whitespace or patch-integrity problems

## Review Checkpoint Note

`plan-eng-review` was not separately run for this phase.

Reason:

- the change is intentionally narrow and does not alter the preview/approval/
  finalization architecture
- the main risk is contract drift inside one generated runner artifact, which is
  better addressed here with focused tests plus pre-merge diff review than with
  a new architecture pass

Pre-merge review checkpoint outcome:

- in-session diff review found no blocking structural issues in the runner,
  gate wiring, or backlog transition

## Remaining Risk

This phase hardens the current generated runner artifact and the repo's local
gates. It does not prove that a future governed execute will be fully clean.

The next governed validation or production-use decision should still rely on the
then-current preview evidence rather than assuming no new review concerns can
appear.

## Conclusion

`BL-20260324-021` is complete as a runner-contract hardening phase:

- dry-run and zero-input outcomes are now honestly reviewable `partial` states
- delegate path resolution no longer depends on `Path.cwd()`
- the readonly preview contract is enforced through reviewed-script delegation
- focused regression coverage now protects the behavior in local gates and CI

The next step is no longer "fix known runner contract drift." The next step, if
needed, is another governed validation or production-use decision against the
current preview state.
