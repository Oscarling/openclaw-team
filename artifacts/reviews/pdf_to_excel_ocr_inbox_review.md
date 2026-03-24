# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

Reviewed `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` using the provided artifact snapshot. The review covers whether the script aligns with the stated best-effort, evidence-backed, read-only preview smoke intent and whether its behavior is appropriately constrained and reviewable.

## Findings

1. **Positive: constrained wrapper design**
   - The script acts as a wrapper around a preferred base script instead of re-implementing OCR/conversion logic.
   - It emits a structured JSON summary with discovery, execution, output, and notes fields.
   - It avoids claiming success unless both the delegate exits with code `0` and the expected `.xlsx` file exists.
   - It explicitly refuses mismatched output extensions and avoids unsupported fallback conversion when the base script is missing.

2. **Positive: evidence-oriented reporting**
   - The summary records discovered PDFs, command execution details, delegate stdout/stderr, and output file presence.
   - Dry-run mode is clearly represented and documented in notes.
   - This is consistent with the instruction not to claim OCR success without evidence.

3. **Issue: success on dry-run may be misleading for automation contracts**
   - When `--dry-run` is used, the script returns `status = "success"` without producing an XLSX output.
   - While the note says no conversion was attempted, some pipelines may interpret `success` as artifact production success.
   - A more contract-safe approach would be a distinct partial/reviewable status in the summary model, or clearer separation between runner success and conversion success.

4. **Issue: runner status model is narrower than review contract expectations**
   - Internally the script only emits `success` or `failed`.
   - The surrounding review contract explicitly recognizes `success`, `partial`, and `failed`.
   - Because this wrapper is for best-effort evidence-backed execution, lack of a `partial` state reduces fidelity for reviewable intermediate outcomes.

5. **Issue: delegate path resolution may be brittle**
   - `preferred_base_script` is resolved relative to `Path.cwd()` when not absolute.
   - That can work in repository-root execution, but is fragile if invoked from another working directory.
   - A more robust implementation would resolve relative to the runner file or repository root explicitly.

6. **Issue: no explicit readonly guarantee beyond metadata intent**
   - The script carries readonly/source metadata in the summary but does not enforce or validate that the delegated base script itself is readonly.
   - Since it shells out to another script, the readonly guarantee is only indirect unless the base script is also reviewed/controlled.

7. **Issue: limited validation of discovered-input edge cases**
   - If zero PDFs are discovered, the script still delegates rather than failing fast or marking a reviewable partial condition.
   - That may be acceptable if the base script handles it, but the wrapper could provide clearer evidence-backed behavior by short-circuiting with an explicit note.

## Verdict

**needs_revision**

## Rationale

The artifact is credible and mostly aligned with a best-effort, evidence-backed wrapper pattern. It shows good discipline in summary generation, refusal to fabricate success, and reuse of an existing repository script.

However, it does not fully meet a strong review pass because:

- dry-run returns `success` without output creation,
- there is no `partial` status for honest reviewable intermediate outcomes,
- base script resolution is environment-sensitive,
- readonly behavior is not enforced beyond intent metadata,
- zero-input handling could be clearer and more deterministic.

These are revision-level concerns rather than total failure because the script is functional, reviewable, and cautious about unsupported claims.
