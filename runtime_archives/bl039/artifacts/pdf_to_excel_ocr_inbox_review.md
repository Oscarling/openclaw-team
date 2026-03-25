# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

Reviewed the following artifacts together as a single readonly smoke execution pair:

- `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- `artifacts/scripts/pdf_to_excel_ocr.py`

Review focus:

- end-to-end readonly wrapper/delegate behavior
- evidence-backed success/partial/failed reporting
- alignment with the stated smoke contract
- determinism and reviewability of local-artifact execution

## Findings

### Positive findings

1. **Readonly delegation pattern is clear and bounded**
   - The wrapper only resolves and invokes the reviewed local delegate script.
   - No Trello writeback or external mutation behavior appears in either artifact.
   - The wrapper uses a bounded subprocess timeout (`--delegate-timeout`), which is appropriate for smoke execution control.

2. **Good structured reporting for reviewability**
   - The wrapper emits a structured JSON summary with request, traceability, discovery, execution, delegate report, logs, and notes.
   - The delegate emits structured JSON to stdout and optionally to a sidecar path via `--report-json`.
   - Dry-run and zero-PDF cases are handled as `partial`, which matches a conservative evidence-backed posture.

3. **Discovery and per-file isolation are sensible**
   - Both wrapper and delegate perform recursive PDF discovery.
   - Delegate processing isolates failures per file and aggregates status without aborting the whole batch.

4. **Delegate avoids unsupported OCR claims**
   - OCR runtime dependencies are detected and surfaced.
   - OCR failure is reported explicitly in per-file results.
   - The delegate reports `partial` when extraction is incomplete rather than overstating success.

5. **Wrapper avoids writing mismatched fake XLSX content**
   - The wrapper itself does not synthesize non-XLSX payloads into the target path.
   - Output writing responsibility remains with the delegate.

### Issues requiring revision

1. **Wrapper success classification is weaker than its own contract suggests**
   - In `evidence_status_from_delegate`, if the delegate report has `status == "success"` and no failed/error-like counts in `status_counter`, the wrapper returns `success`.
   - It does **not** additionally verify delegate evidence such as:
     - `excel_written == true`
     - `output_exists == true`
     - `output_size_bytes > 0`
   - This is important because the wrapper header explicitly claims "stronger success evidence from delegate JSON report fields", but current logic does not enforce those output-evidence fields.
   - Result: the wrapper may classify a run as `success` based only on aggregate delegate status, even if output evidence is absent or inconsistent.

2. **Wrapper execution summary checks local output existence but does not use it to gate success**
   - `build_summary()` captures `output_exists` and `output_size`, which is useful.
   - However, these values do not affect `final_status` when delegate JSON is present.
   - This means observable local evidence is collected but not used to protect the success verdict.

3. **Delegate can report aggregate success before write phase, but wrapper trusts final report too broadly**
   - The delegate initially sets aggregate status from file-level results, then attempts Excel writing.
   - It does downgrade to `failed` on write exception, which is good.
   - Still, because the wrapper is intended to be the reviewable inbox layer, it should independently verify the delegate's reported output evidence rather than trusting `status` alone.

### Minor observations

- The wrapper appends a note if `--output-xlsx` does not end with `.xlsx`, but does not fail fast. This is acceptable for a best-effort wrapper, though stricter validation could be justified.
- The wrapper contains an unreachable `if args.dry_run:` inside the delegate command assembly because dry-run is short-circuited earlier; harmless but unnecessary.
- The delegate imports optional dependencies defensively and degrades reasonably.

## Verdict

**needs_revision**

## Rationale

The pair is close to acceptable for a readonly, reviewable smoke path and demonstrates strong conservative design in several areas: structured reporting, bounded execution, local-only delegation, explicit dry-run/partial handling, and no inflated OCR claims.

However, the wrapper's central evidence-handling responsibility is not fully met. It claims stronger success evidence based on delegate JSON, yet its actual success decision does not require proof that a real Excel artifact was written. Because the smoke contract explicitly says not to claim success without evidence, this is a material review issue.

### Recommended revision

Tighten wrapper success logic so `success` requires all of the following when delegate JSON is present:

- delegate report `status == "success"`
- `total_files > 0`
- no failed/error/timeout counts in `status_counter`
- `excel_written == true`
- `output_exists == true`
- `output_size_bytes > 0`
- ideally, local wrapper-side `output_xlsx.exists()` and nonzero size agree with delegate evidence

If those conditions are not met, downgrade to `partial` or `failed` with an explicit note.

With that adjustment, this wrapper/delegate pair would be much better aligned with the stated evidence-backed readonly smoke contract.