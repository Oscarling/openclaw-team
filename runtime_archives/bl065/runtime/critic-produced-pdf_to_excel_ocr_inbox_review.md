# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope
- Primary artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- Paired artifact: `artifacts/scripts/pdf_to_excel_ocr.py`
- Review mode: end-to-end readonly smoke-path audit using supplied snapshots
- Objective: assess whether the wrapper and delegate together provide a deterministic, evidence-backed, readonly reviewable path for PDF-to-Excel OCR smoke execution

## Findings

### Strengths
1. **Readonly intent is explicit and mostly credible**
   - The wrapper clearly documents readonly semantics as "no external/Trello writeback" while allowing local output.
   - No Trello/network writeback logic is present in either script.
   - Traceability fields (`origin_id`, `title`, `description`, `labels`) are preserved into the wrapper runtime summary.

2. **Evidence-backed reporting is substantially implemented**
   - The delegate emits structured JSON with extraction/export state, per-file outcomes, OCR runtime status, workbook attestation fields, and next steps.
   - The wrapper prefers sidecar JSON and falls back to parsing JSON from stdout, which is appropriate for reviewability.
   - The wrapper adds preflight PDF discovery evidence and preserves delegate command context.

3. **Best-effort semantics are generally honest**
   - The delegate avoids claiming success when no text is extracted.
   - OCR runtime detection is explicit, with missing dependency reporting.
   - Dry-run behavior is clearly separated from actual workbook generation.
   - The wrapper downgrades outcomes to partial when OCR/runtime evidence is incomplete, which aligns with the "do not claim success without evidence" contract.

4. **Batch isolation and per-file reporting are good**
   - The delegate processes PDFs independently and accumulates results rather than failing the whole batch on first error.
   - Per-file `status`, `warnings`, `error`, preview, and extraction method fields provide useful audit evidence.

### Issues requiring revision
1. **Wrapper exit/status semantics are inconsistent with delegate process outcome**
   - In the normal path, the wrapper evaluates success/partial/failed from the delegate report, but it does not treat a non-zero delegate exit code as a hard signal if JSON is available.
   - Example: the delegate can exit non-zero while still writing JSON; the wrapper may still derive `partial` or potentially other outcomes from report content alone.
   - For an inbox runner acting as a reviewed wrapper, subprocess exit code should be incorporated into the evidence gate, or there should be a documented reason to trust JSON over process failure.
   - This is the most important end-to-end issue because it weakens determinism of automation control flow.

2. **The wrapper can classify delegate no-input as failed instead of preserving delegate partial semantics**
   - Delegate behavior for no PDFs: emits `status=partial`, returns exit code `0`.
   - Wrapper behavior for no discovered PDFs: returns `partial` only if no delegate report is needed, but in its evaluation branch if `delegate_report is None` it becomes `failed`; more importantly, wrapper preflight is separate from delegate invocation semantics and can produce a different operational interpretation than the delegate.
   - The scripts are close here, but the pair does not fully guarantee a single canonical meaning for no-input conditions.

3. **Wrapper does not include stderr/stdout in successful/partial structured report except indirectly**
   - If delegate emits stderr but still returns a report, the wrapper merely appends a limitation note.
   - For auditability, captured stderr/stdout should be preserved in runtime summary or delegated report metadata when relevant.
   - This is especially important for best-effort smoke reviews where limitations are part of the contract.

4. **Status typing annotation is imprecise**
   - `_evaluate_outcome` is annotated as returning `(str, List[str], List[str])` rather than a `Tuple[...]` type. This is minor and non-runtime-breaking in practice, but it reflects review-quality looseness.

5. **Potential duplicate discovery ordering in wrapper**
   - `_discover_pdfs` concatenates recursive `*.pdf` and `*.PDF` matches. On case-insensitive filesystems this could theoretically duplicate the same file path.
   - The delegate's own discovery uses suffix normalization and is cleaner/canonical.
   - Since the wrapper only uses discovery for preflight evidence, impact is low, but it is still an avoidable inconsistency between wrapper and delegate.

### Delegate-specific observations
- The delegate is generally solid for a best-effort reviewable extractor.
- It correctly separates extraction and export states and avoids overstating OCR success.
- One subtle semantics issue: `status` is set from extraction outcome first, then may be forced to `failed` on export failure. This is acceptable, but downstream consumers must understand that top-level `status` represents overall run, while `extraction_status` preserves extraction-only truth.

## Verdict
**needs_revision**

## Rationale
The overall design is thoughtful and largely aligned with the requested readonly, evidence-backed smoke contract. The delegate script in particular provides credible audit evidence and cautious OCR/export claims. However, the wrapper is the inbox-facing control surface, and its treatment of subprocess exit code versus structured report evidence is not strict enough for a robust end-to-end reviewed runner. That mismatch means the pair is not yet strong enough to receive a full pass.

A pass would be more justified after:
1. Making delegate non-zero exit codes part of the wrapper outcome gate, even when JSON exists.
2. Tightening canonical semantics for no-input / partial / failed cases across both scripts.
3. Preserving relevant stderr/stdout diagnostics in the wrapper's structured summary.
4. Cleaning minor consistency issues such as duplicate discovery risk and type annotation precision.
