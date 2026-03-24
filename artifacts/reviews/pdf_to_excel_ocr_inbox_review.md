# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope
Review of the automation artifact `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` against the stated best-effort, evidence-backed, readonly Trello smoke objective for PDF extraction/conversion preview output.

## Findings
- The script is grounded in local-only behavior and does not perform Trello writeback. It uses fixed metadata fields and reads PDFs from a local desktop directory.
- It detects local tools (`pdftotext`, `pdfinfo`, `pdftoppm`, `tesseract`) and records tool paths in output, which supports evidence-backed reviewability.
- It avoids claiming OCR success without extracted text evidence. OCR success is only marked when text is actually recovered.
- It emits a spreadsheet-like output containing extraction status, method, notes, and text preview, which aligns with the requirement for reviewable intermediate artifacts.
- If no PDFs are present, it still writes a header-only workbook and warns accordingly, which is consistent with best-effort behavior.
- However, the declared output path is `artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx`, but the writer generates SpreadsheetML XML text directly via `write_text`. This is not a real XLSX container and may mislead downstream consumers expecting a true `.xlsx` file.
- The script hardcodes `INPUT_DIR` to `~/Desktop/pdf样本`, which reduces determinism/portability in managed automation contexts and may not match declared local artifacts unless the environment is prepared exactly.
- The description field from input metadata is truncated to `"Purpose:"` rather than preserving the fuller task context, weakening traceability.
- No execution evidence or produced output workbook artifact was provided alongside the script, so review is limited to code inspection rather than validation of runtime behavior.

## Verdict
**needs_revision**

## Rationale
The script shows good-faith alignment with the readonly, best-effort, evidence-backed extraction objective and includes review-oriented status reporting. But it has material issues that prevent a full pass: the `.xlsx` extension does not match the actual file format produced, the local input path is overly environment-specific, and there is no runtime evidence demonstrating that the artifact successfully produced the intended reviewable output in this pipeline run. These are revision-level issues rather than a complete failure because the core extraction/review logic is present and generally honest about limitations.
