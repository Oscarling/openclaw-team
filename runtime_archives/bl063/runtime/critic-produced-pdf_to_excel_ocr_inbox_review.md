# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

Reviewed the generated inbox runner (`artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`) together with its paired reviewed delegate (`artifacts/scripts/pdf_to_excel_ocr.py`) as one end-to-end readonly local inbox smoke path.

The review focused on:
- readonly Trello/local inbox semantics
- wrapper-to-delegate contract compatibility
- evidence-backed success/partial/failure handling
- OCR claim discipline
- whether the pair supports a reviewable best-effort smoke without overstating success

## Findings

1. **Good: wrapper preserves readonly external semantics**
   - The runner embeds request metadata and explicitly states no external/Trello writeback.
   - It limits activity to local discovery and local file output, matching the stated smoke scope.
   - It refuses to substitute a missing delegate with arbitrary behavior, which is appropriate for controlled reviewable execution.

2. **Good: delegate is structured for best-effort evidence-backed execution**
   - The delegate emits structured JSON with `status`, `total_files`, `status_counter`, `dry_run`, OCR runtime state, notes, and next steps.
   - It avoids claiming OCR success when OCR dependencies are missing; instead it reports `ocr_runtime_status` and missing dependencies.
   - Batch isolation is present: one file failure does not halt all processing.

3. **Good: wrapper correctly avoids overstating success**
   - The runner requires multiple gates before returning success, including delegate status, non-dry-run, nonzero files, zero partial/failed counts, and a real XLSX output.
   - It downgrades OCR-limited situations to partial rather than success.
   - This aligns well with the request’s instruction not to claim OCR/conversion success without evidence.

4. **Issue: wrapper can misclassify some legitimate delegate outcomes as `failed`**
   - The delegate sets aggregate status to `partial` whenever any file is `partial` or `failed`, even if an Excel file is still successfully written.
   - The wrapper only has an explicit partial-preservation branch for `delegate_status == "partial"`, plus a separate dry-run/zero-PDF branch.
   - But when the delegate returns `failed` specifically because the Excel write step failed after otherwise reviewable extraction, the wrapper falls through to wrapper-level `failed`.
   - That is defensible for workbook production, but it compresses a potentially useful reviewable intermediate state into failure without distinguishing extraction evidence from export failure.

5. **Issue: wrapper/output path policy is only partially readonly-safe**
   - The wrapper states local filesystem writes are possible and defaults output under `artifacts/outputs/...`, which is fine for local smoke.
   - However, `_expand_path` resolves the input path against the host environment and `--output-xlsx` may be absolute, so the pair permits arbitrary local write destinations if called with an absolute path.
   - This does not violate the stated no-external-writeback contract, but it is broader than a tightly sandboxed “declared local artifacts only” interpretation.

6. **Issue: delegate success semantics are extraction-centric, wrapper success semantics are workbook-centric**
   - Delegate aggregate `success` means no per-file partial/failed results, not necessarily that Excel was written yet.
   - The wrapper compensates by additionally checking `excel_written`, `output_exists`, and size > 0.
   - This works, but the contract between the two scripts is implicit rather than unified. A future change in delegate report fields could break wrapper interpretation.

7. **Issue: actual smoke evidence is not present in the reviewed material**
   - The scripts are reviewable and plausibly implement the desired path, but no execution report, sample stdout, sidecar JSON, discovered PDF list from a run, or generated XLSX artifact was supplied.
   - Therefore this review can validate implementation logic only, not an actual successful end-to-end smoke outcome.

## Verdict

**needs_revision**

## Rationale

The pair is generally well aligned with the best-effort, evidence-backed, readonly smoke contract. In particular, it shows disciplined handling of OCR uncertainty and avoids claiming success without structured evidence.

However, this is not a clean pass because:
- the wrapper/delegate contract is not fully normalized and relies on wrapper-side interpretation of delegate fields;
- absolute output paths allow broader local writes than a stricter declared-artifacts-only policy would suggest;
- some reviewable intermediate outcomes are collapsed into wrapper-level failure instead of being more explicitly preserved;
- no actual run evidence was supplied, so end-to-end smoke behavior cannot be fully verified beyond static review.

Recommended revisions:
1. Tighten output path policy so writes are restricted to an approved artifact subtree unless explicitly overridden by a governed flag.
2. Normalize the delegate report contract so workbook-write outcome is a first-class aggregate status dimension, not inferred by the wrapper.
3. Preserve extraction-vs-export distinction more clearly in wrapper summaries when Excel writing fails after partial extraction evidence exists.
4. Add an example execution artifact (JSON report and/or sample XLSX metadata) to support a stronger end-to-end review in future runs.
