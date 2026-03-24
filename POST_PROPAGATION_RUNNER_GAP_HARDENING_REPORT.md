# Post-Propagation Runner Gap Hardening Report

## Objective

Close `BL-20260324-024` by hardening the source-side runner contract and the
execute-time critic assembly around the four residual concerns exposed by
`BL-20260324-023`:

- delegate review evidence did not include the reviewed base script
- wrapper success evidence was still too weak
- the generated default description still arrived truncated
- delegate subprocess execution had no timeout bound

This phase is a hardening phase, not a new governed live validation.

## Scope

In scope:

- source-side contract updates in `adapters/local_inbox_adapter.py`
- execute-time critic artifact assembly updates in
  `skills/execute_approved_previews.py`
- baseline runner hardening in
  `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- regression tests and merge gates for the new contract

Out of scope:

- a new live Trello regeneration / approval / execute round
- Git finalization
- Trello writeback / Done

## Root Cause Summary

The residual `needs_revision` concerns from `BL-20260324-023` were not all in
the same layer.

1. Description truncation came from the source adapter:
   `_condense_automation_description(...)` normalized the description but still
   defaulted to a 180-character ceiling, which produced the `cla...` suffix in
   the fresh generated runner.
2. Missing delegate review evidence was an execute-time assembly problem:
   even if a critic task declared multiple artifacts, `build_critic_from_automation(...)`
   replaced them with automation output artifacts, so the reviewed delegate
   script was silently dropped from the actual critic snapshot set.
3. Weak success evidence and missing timeout were still under-specified in the
   propagated contract, so the generated runner could remain too permissive even
   after earlier hardening phases.

## Changes

### 1. Source-side contract hardening

`adapters/local_inbox_adapter.py` now:

- preserves the normalized description context by default instead of truncating
  it to 180 characters
- adds explicit contract hints for:
  - stronger delegate success evidence
  - explicit delegate timeout behavior
- upgrades automation constraints and acceptance criteria so future generated
  runners are asked to:
  - avoid claiming success from exit code plus file existence alone
  - bound delegate execution time explicitly

### 2. Critic review-scope hardening

The critic task now declares both:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `artifacts/scripts/pdf_to_excel_ocr.py`

And `skills/execute_approved_previews.py` now preserves predeclared critic
artifacts when merging in automation outputs. This means execute-time review can
see both the wrapper and the reviewed delegate instead of silently collapsing to
the wrapper snapshot only.

### 3. Baseline runner hardening

`artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` now:

- preserves a non-truncated default description with traceability context
- enforces stronger delegate success evidence before reporting wrapper success:
  - structured delegate report must exist
  - `status=success`
  - `total_files >= 1`
  - no failed-file evidence in `status_counter`
  - not a delegate dry run
- adds `--delegate-timeout-seconds` and treats timeout as an explicit failed
  outcome instead of hanging indefinitely

These baseline changes provide a stronger reference contract for future
generated runners and keep the tracked repo artifact aligned with the intended
review standard.

### 4. Regression coverage and gates

Added or expanded coverage in:

- `tests/test_local_inbox_adapter.py`
- `tests/test_pdf_to_excel_ocr_inbox_runner.py`
- `tests/test_execute_approved_previews.py`

And added `tests/test_execute_approved_previews.py` to:

- `scripts/premerge_check.sh`
- `.github/workflows/ci.yml`

## Verification

Passed on 2026-03-24:

- `python3 -m unittest -v tests/test_local_inbox_adapter.py`
- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`
- `python3 -m unittest -v tests/test_execute_approved_previews.py`
- `python3 -m unittest -v tests/test_argus_hardening.py`
- `bash scripts/premerge_check.sh`

Observed gate result:

- `Warnings: 0`
- `Failures: 0`

## Conclusion

`BL-20260324-024` can be treated as complete as a source hardening phase.

The repo now preserves fuller description context, keeps the reviewed delegate
in critic scope at execute time, requires stronger delegate evidence for wrapper
success, and bounds delegate runtime with an explicit timeout.

The next correct step is not to mutate this phase further. It is a new governed
validation phase on a fresh same-origin preview candidate so the project can
verify that these tightened rules actually propagate into the next generated
runner and clear the post-propagation review concerns in live execution.
