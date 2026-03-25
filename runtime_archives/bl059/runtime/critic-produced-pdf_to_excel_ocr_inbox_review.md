# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

This review evaluates the supplied wrapper `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` together with its paired reviewed delegate `artifacts/scripts/pdf_to_excel_ocr.py` as one end-to-end readonly smoke path, per the review contract.

Artifacts reviewed:
- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `artifacts/scripts/pdf_to_excel_ocr.py`

Review focus:
- alignment with the stated best-effort, evidence-backed, readonly smoke contract
- honesty of success/partial/failure signaling
- wrapper/delegate compatibility
- whether the pair produces reviewable evidence without overstating OCR or business completion

## Findings

### 1. Strong points in the wrapper

- The wrapper is conservative about success claims.
- It requires structured JSON evidence from the delegate, preferring a sidecar report and falling back to stdout JSON parsing.
- It refuses success unless multiple evidence gates are met: delegate status `success`, `total_files >= 1`, `dry_run is False`, no failed or partial counts, `excel_written=true`, `output_exists=true`, and positive output size.
- It preserves honest partial outcomes instead of upgrading them to success.
- It includes limitations and next steps in failure/partial paths.
- It keeps execution local and does not perform Trello writeback.

These behaviors align well with the requested “best-effort, evidence-backed” contract.

### 2. Delegate supports structured, reviewable execution

- The delegate exposes explicit CLI parameters for input directory, output path, OCR mode, dry-run, OCR language, threshold, and `--report-json`.
- It discovers PDFs locally and isolates processing per file.
- It emits structured JSON including aggregate status, per-file records, OCR runtime information, counters, notes, and next steps.
- It correctly returns `partial` when no PDFs are found.
- It avoids claiming OCR success directly when extraction/OCR errors occur; file-level statuses can become `partial` or `failed`.

This is generally compatible with reviewable smoke execution.

### 3. Material contract mismatch: readonly path vs local output mutation

This is the main issue.

The wrapper presents itself as a:
- “Readonly reviewable inbox wrapper”
- readonly smoke path
- no business execution claim
- no Trello writeback

While no Trello writes occur, the end-to-end pair is not strictly readonly in the broader execution sense because the delegate writes a local XLSX in non-dry-run mode, and the wrapper defaults to non-dry-run execution.

Evidence:
- wrapper default output path: `artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx`
- wrapper invokes delegate without forcing `--dry-run`
- delegate writes Excel unless `--dry-run` is passed

So the pair is readonly with respect to Trello/external system mutation, but not readonly with respect to the local filesystem. If the intended contract is “read-only Trello ingest only,” this may be acceptable; if the intended contract is a stricter readonly smoke, the naming and runtime summary overstate the property.

### 4. Wrapper runtime summary may overstate readonly behavior

The wrapper always reports in `runtime_summary`:
- `reviewable: True`
- `readonly_flow: True`
- `best_effort: True`

`readonly_flow: True` is unconditional, even when the delegate writes a real XLSX. That makes the summary semantically questionable unless readonly is narrowly defined as “no source-system writeback.” The script does not explicitly document that narrower definition in the JSON summary.

### 5. Success can still be conditional on incomplete OCR certainty

The delegate may return aggregate `success` when all files have non-empty extracted text and no per-file errors, even if OCR runtime is unavailable. In some cases this is fine because direct text extraction may be enough. But for image-only PDFs, lack of OCR runtime could mean incomplete extraction without definitive detection.

The delegate does report OCR runtime status and missing dependencies, which is good. However:
- aggregate `success` does not require OCR availability when OCR might have been needed semantically
- the wrapper also does not inspect `ocr_runtime_status`

This means the pair is honest about available evidence, but not maximally rigorous for OCR completeness claims across mixed PDF types.

### 6. Wrapper/delegate interface compatibility is otherwise good

The wrapper calls the delegate with:
- `--input-dir`
- `--output-xlsx`
- `--ocr`
- `--report-json`
- optional `--dry-run`

The delegate supports all of these, so the integration is mechanically consistent.

### 7. Partial/failure handling is stronger than success handling semantics

The overall design is cautious and review-friendly. The main weakness is not hidden failure handling, but terminology/contract clarity:
- “readonly” is underspecified and potentially misleading
- wrapper success does not consider OCR runtime sufficiency
- wrapper success depends on delegate attestations rather than independently validating workbook contents beyond existence/size

These are revision-level concerns, not total failure.

## Verdict

**needs_revision**

## Rationale

The reviewed pair is substantively competent and evidence-oriented, and it does not appear to fabricate success. The wrapper is especially strong in preserving honest partial/failure states and requiring structured delegate evidence.

However, I cannot issue `pass` because there is a meaningful contract ambiguity/inconsistency in the claimed readonly smoke path:
- the wrapper describes the flow as readonly,
- but by default it runs non-dry-run and causes local XLSX output mutation,
- while also unconditionally reporting `readonly_flow: True`.

In addition, end-to-end success does not account for OCR runtime sufficiency, so the pair can produce a formally successful outcome that is operationally weaker than the “do not claim OCR success without evidence” intent for certain PDF classes.

Recommended revisions:
1. Clarify readonly semantics explicitly as “no external/Trello writeback” if local artifact creation is intended.
2. Change `runtime_summary.readonly_flow` so it reflects actual semantics, or rename it to something like `no_external_writeback`.
3. Consider forcing `--dry-run` by default in the wrapper if the smoke is intended to remain strictly preview-only.
4. Consider surfacing `ocr_runtime_status` in wrapper gating or at least in wrapper limitations when OCR dependencies are missing.
5. Optionally strengthen success evidence by validating workbook readability, not just existence/size.

Given the above, the correct structured verdict is `needs_revision`, not `fail`, because the pair is largely sound and reviewable but not fully aligned with the stated contract.