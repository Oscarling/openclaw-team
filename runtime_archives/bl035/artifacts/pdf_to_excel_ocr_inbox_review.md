# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

Reviewed the following artifacts together as a readonly end-to-end pair, per review scope:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `artifacts/scripts/pdf_to_excel_ocr.py`

Assessment focus:

- wrapper/delegate alignment
- readonly smoke-path honesty
- evidence-backed success/failure semantics
- deterministic local-artifact behavior
- JSON/reporting behavior suitable for reviewability

## Findings

### Strengths

1. **Wrapper preserves readonly, reviewable behavior well**
   - No Trello writeback behavior is present.
   - Control flow is local-artifact oriented and deterministic.
   - The wrapper explicitly avoids claiming success from process exit code alone.
   - It requires canonical delegate evidence fields (`status`, `total_files`, `status_counter`, `dry_run`) and also checks XLSX existence/size.

2. **Good preflight and partial-outcome handling in wrapper**
   - Dry-run returns `partial` honestly without delegation.
   - Missing input directory returns `failed`.
   - Zero discovered PDFs returns `partial` with explicit notes instead of falsely claiming success.
   - Delegate timeout is bounded and reported.

3. **Good path resolution and reporting ergonomics in wrapper**
   - Relative path handling is designed to be independent of `Path.cwd()`.
   - Optional wrapper sidecar reporting is supported.
   - Delegate stdout and sidecar JSON are both considered as evidence sources.

4. **Delegate has solid batch-processing foundations**
   - Recursive PDF discovery.
   - Per-file isolation via `FileResult` and exception capture.
   - OCR modes `auto|on|off` and Chinese-friendly default OCR language.
   - JSON report emission to stdout and optional sidecar.
   - Excel output includes summary and per-file sheets.

### Issues

1. **Zero-input semantics are misaligned between wrapper and delegate**
   - Wrapper contract intentionally treats zero discovered PDFs as an honest `partial` outcome.
   - Delegate emits:
     - `status: "failed"`
     - return code `2`
     when no PDFs are found.
   - This creates an end-to-end semantic mismatch for the readonly smoke path, where zero inputs should remain reviewable rather than be treated as a hard failure.

2. **Delegate overall status can overstate success when partial files exist**
   - Delegate computes overall status as:
     - `success` if `failed == 0`
     - otherwise `partial`
   - This ignores `partial` file results.
   - Therefore a batch with one or more `partial` items and zero `failed` items will be reported as overall `success`, which is too optimistic for an evidence-backed contract.
   - The wrapper compensates by checking `status_counter.partial == 0` before declaring wrapper success, but this means the pair relies on wrapper correction of delegate semantics rather than consistent delegate truthfulness.

3. **Delegate report does not directly attest to write success beyond status/error fields**
   - The wrapper requires actual XLSX file existence and non-zero size, which is good.
   - But the delegate’s canonical report omits an explicit `excel_written: true/false` or similar field.
   - As a result, the success contract is split across delegate JSON plus wrapper filesystem checks rather than being fully self-describing in delegate evidence.

4. **Dry-run semantics in delegate are somewhat broad but acceptable**
   - Delegate still processes PDFs in dry-run mode and only skips Excel writing.
   - This is not incorrect, but the wrapper’s own dry-run means “do not delegate at all,” so there are two different dry-run layers with different meanings.
   - That can be reviewable, but should be documented more explicitly to avoid confusion.

5. **Per-file details are not included in delegate’s canonical report**
   - The delegate computes detailed `FileResult` rows, but the JSON report only contains aggregate counters.
   - For a best-effort, evidence-backed smoke path, a compact per-file summary in the report would improve auditability, especially when Excel writing fails or is skipped.

## Verdict

**needs_revision**

## Rationale

The wrapper is thoughtfully implemented and strongly aligned with the readonly, evidence-backed smoke contract. It is cautious about success claims, handles partial scenarios honestly, and evaluates delegate output more rigorously than the delegate itself.

However, when reviewed as the required end-to-end pair, there are notable semantic inconsistencies that prevent a full pass:

- zero-input handling is `partial` in the wrapper conceptually but `failed` in the delegate,
- delegate batch status can incorrectly report `success` even when partial file outcomes exist,
- canonical report evidence could be stronger and more self-describing.

These are revision-level issues rather than total failure because the wrapper already mitigates some of the delegate weaknesses and the overall design is close to the stated contract.

## Recommended revisions

1. Change delegate zero-PDF outcome from hard `failed` to an honest reviewable `partial` status, or otherwise align both components on one documented contract.
2. Change delegate aggregate status logic so any `partial` file result prevents overall `success`.
3. Add explicit output-write evidence in delegate report, such as `excel_written`, `output_exists`, and `output_size_bytes` after write.
4. Optionally include lightweight per-file results in the delegate JSON report to improve reviewability without requiring Excel inspection.
5. Clarify dry-run semantics between wrapper dry-run and delegate dry-run in comments/help text.
