# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope
- Primary artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- Paired artifact: `artifacts/scripts/pdf_to_excel_ocr.py`
- Review basis: supplied artifact snapshots only
- Review goal: assess the wrapper and delegate together as one end-to-end readonly smoke path

## Findings

### Positive findings
1. The wrapper is explicitly readonly in intent and only invokes a local reviewed delegate via a resolved script path.
2. The wrapper performs useful preflight checks for input directory existence, PDF discovery, delegate presence, and `.xlsx` output suffix.
3. The wrapper enforces evidence-based success promotion. It only returns `success` when the delegate report satisfies concrete gates such as:
   - `status == success`
   - `total_files >= 1`
   - `dry_run is false`
   - no failed/partial counters
   - `excel_written == true`
   - `output_exists == true`
   - `output_size_bytes > 0`
4. The wrapper preserves partial outcomes honestly and includes limitations/next steps instead of overstating OCR or Excel success.
5. The delegate script is consistent with the requested best-effort/evidence-backed behavior:
   - batch processing with per-file isolation
   - optional OCR fallback
   - structured JSON report to stdout and optional sidecar
   - explicit `excel_written`, `output_exists`, and `output_size_bytes` fields
   - partial status when extraction is incomplete rather than falsely claiming success
6. The delegate’s aggregate report structure aligns well with the wrapper’s parser and evidence gates.

### Issues requiring revision
1. **End-to-end dry-run contract mismatch**
   - The delegate supports `--dry-run` and reports `dry_run` in its JSON.
   - The wrapper accepts `--dry-run`, but when `args.dry_run` is set it short-circuits before delegate execution rather than forwarding the flag.
   - More importantly, in the normal delegated command the wrapper never appends `--dry-run` to the delegate command.
   - This means the wrapper/delegate pair does not preserve the delegate CLI contract end-to-end. The wrapper has its own dry-run behavior instead of passing through the reviewed delegate mode.
   - For an inbox runner intended to audit the reviewed delegate together, this is a real integration gap.

2. **Status vocabulary inconsistency across pair**
   - Wrapper internal status values include `success`, `partial`, and `failed`.
   - Delegate also emits `failed` in some cases.
   - This is workable, but the wrapper’s `finalize()` maps anything other than `success` and `partial` to exit code 1, while still printing JSON status text. The pair would be cleaner with one explicitly documented shared status vocabulary.

3. **Wrapper relies on canonical fields but only partially validates report shape**
   - The wrapper says canonical fields are `status`, `total_files`, `status_counter`, and `dry_run`.
   - It does not fail early if some of those fields are absent; instead it derives falsy values and later fails gates.
   - This is acceptable defensively, but weaker than a direct schema check.

### Non-blocking observations
1. The wrapper uses `parse_json_text()` on stdout and falls back to the sidecar file, which is a practical robustness measure.
2. The delegate sets aggregate `status` to `partial` whenever any file is partial or failed, which is conservative and aligns with the evidence-backed policy.
3. The delegate’s Excel write path depends on pandas and likely an Excel engine; failure handling is explicit and honest.

## Verdict
**needs_revision**

## Rationale
The pair demonstrates strong evidence-backed design and mostly satisfies the readonly smoke intent. However, the review scope explicitly requires evaluating the wrapper and reviewed delegate together. Under that end-to-end standard, the wrapper does not faithfully expose the delegate’s dry-run execution mode and instead substitutes its own short-circuit path. That integration mismatch is significant enough to prevent a full pass, but it is not severe enough to mark the artifact pair as a hard fail because the overall behavior remains cautious, local, readonly, and honest about limitations.

Recommended revision:
- Forward `--dry-run` to the delegate when requested, or explicitly document that wrapper dry-run is a wrapper-only preflight mode distinct from delegate dry-run.
- Optionally add explicit report schema validation and unify documented status vocabulary across wrapper and delegate.
