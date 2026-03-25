# Wrapper Provenance/Path Traceability Hardening Report

## Objective

Complete `BL-20260325-050` by hardening wrapper provenance/path traceability
semantics after `BL-20260325-049` critic findings, while preserving existing
best-effort evidence-backed status behavior.

## Scope

In scope:

- remove path-resolution ambiguity for delegate script selection
- strengthen readonly provenance and traceability attestation in wrapper summary
- add focused tests covering path-boundary and traceability contract behavior

Out of scope:

- live governed rerun in this phase
- delegate OCR algorithm changes
- Trello writeback or finalization behavior changes

## Changes

### 1) Path-resolution strategy is now single-rule and audit-visible

Updated `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`:

- replaced implicit path handling with a deterministic delegate resolution model:
  - absolute path -> resolve as absolute
  - relative path -> resolve strictly from `REPO_ROOT`
- added `provenance.delegate_path_resolution` fields in summary:
  - `requested`, `expanded`, `strategy`, `resolved`,
    `within_repo_root`, `repo_relative_path`
- added repository-boundary guard so default reviewed-script mode cannot escape
  the repository root

### 2) Readonly provenance/traceability attestation strengthened

Updated wrapper summary payload with explicit contract evidence:

- `run_id` for stable run traceability
- `provenance` block:
  - `runner_path`, `repo_root`, `origin_id`
  - `delegate_path_resolution`
  - `input_dir_resolution` with discovery mode
- `readonly_attestation` block:
  - `mode = local_filesystem_delegate_only`
  - `network_calls_performed = false`
  - `trello_write_performed = false`
  - `delegate_restricted_to_reviewed_script`
  - explicit statement of local-only behavior

### 3) Delegate report parsing robustness improved

Updated wrapper report parsing:

- still supports whole-stdout JSON object
- now also supports trailing JSON line extraction when stdout includes extra logs

### 4) Focused regressions expanded

Updated `tests/test_pdf_to_excel_ocr_inbox_runner.py`:

- extended path-resolution test to assert deterministic
  `repo_root_relative` strategy and repo-relative resolved path
- added test that rejects delegate path escaping repository root
- added test that enforces provenance/readonly attestation fields
- preserved existing behavior tests for dry-run/partial/success-gating/timeout

## Verification

Passed on 2026-03-25:

- `python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py`
- `python3 scripts/backlog_lint.py`
- `python3 scripts/backlog_sync.py`

## Conclusion

`BL-20260325-050` can be treated as complete as a source-side blocker-hardening
phase.

Wrapper output now carries explicit provenance/path/readonly attestation
semantics, and delegate path resolution is deterministic and boundary-aware.

Next required step: run a fresh same-origin governed validation to verify
whether critic findings shift away from wrapper provenance/path traceability
concerns under real execute.
