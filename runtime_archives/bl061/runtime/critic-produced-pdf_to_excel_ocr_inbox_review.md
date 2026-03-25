# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope

Reviewed the wrapper `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py` together with its paired delegate `artifacts/scripts/pdf_to_excel_ocr.py` as one end-to-end readonly smoke path.

Focus areas:
- readonly/best-effort behavior
- evidence-backed success/partial/failure handling
- wrapper/delegate CLI and report compatibility
- honesty of OCR/Excel success signaling

## Findings

### 1. Positive: wrapper is intentionally conservative and mostly aligned to contract
- The wrapper explicitly frames the flow as readonly-reviewable and states that no external/Trello writeback occurs.
- It discovers PDFs before execution and returns `partial` when none are found, which fits the reviewable smoke contract.
- It forwards `--dry-run` to the delegate instead of falsely claiming success.
- It requires strong evidence before reporting `success`, including:
  - `report.status == "success"`
  - `total_files >= 1`
  - not dry-run
  - no failed/partial counts
  - `excel_written == true`
  - `output_exists == true`
  - `output_size_bytes > 0`
- It downgrades outcomes to `partial` when OCR is blocked/partial or when the delegate itself reports partial status.

### 2. Positive: delegate generally supports evidence-backed reporting
- The delegate emits structured JSON and can also write a sidecar report with `--report-json`.
- It separates per-file outcomes and computes aggregate status.
- It avoids claiming OCR availability when dependencies are missing via `ocr_runtime_status` and `ocr_missing_dependencies`.
- It supports dry-run and does not claim Excel output in dry-run mode.

### 3. Material issue: wrapper/delegate report contract is not fully robust for all delegate outcomes
The wrapper depends heavily on a structured delegate report shape. This is mostly present, but not uniformly strong across all delegate failure modes.

Examples:
- On input discovery exception, the delegate emits only:
  - `{"status": "failed", "error": ...}`
- The wrapper can parse that, but its downstream interpretation expects richer fields such as:
  - `total_files`
  - `status_counter`
  - `excel_written`
  - `output_exists`
  - `output_size_bytes`
  - `ocr_runtime_status`

While the wrapper tolerates missing fields by defaulting many values, this creates an underspecified contract between the pair. For a reviewed wrapper/delegate pair, the report schema should be more consistent across success, partial, and failure paths so wrapper logic is grounded in explicit evidence rather than absent-field defaults.

### 4. Material issue: wrapper may classify some delegate failures too generically
When the delegate returns a sparse failure report, the wrapper falls back to evidence-gate reasons such as:
- `delegate total_files < 1`
- `delegate excel_written is not true`
- `delegate output_exists is not true`

Those are technically true, but they may obscure the actual delegate failure reason already present in `report.error`. The end-to-end review artifact would be stronger if the wrapper surfaced delegate `error` prominently in `limitations` or `next_steps`.

### 5. Minor issue: readonly semantics are accurate but not perfectly scoped
The wrapper states no external/Trello writeback occurs, which is good. It also correctly admits local filesystem writes may occur when `dry_run=false`. That is honest. However, because the delegate always writes report JSON and may write XLSX locally, the pair is readonly only in the external-system sense, not fully side-effect-free. The wording is acceptable but should remain precise in downstream usage.

### 6. Minor issue: success gate is intentionally strict, but schema coupling is high
The wrapper's success gate is commendably strict. However, it is tightly coupled to specific delegate keys. Since both artifacts are reviewed as a pair, this is acceptable only if the delegate schema is treated as stable and consistently emitted. Right now the sparse failure report shape weakens that assumption.

## Verdict

**needs_revision**

## Rationale

This is not a fail because the pair shows strong intent toward governed, evidence-backed, readonly smoke behavior and avoids dishonest OCR/Excel success claims. The wrapper is conservative, uses timeout bounds, preserves partial outcomes, and only reports success on strong evidence.

However, the pair should be revised before being considered a clean pass because the wrapper/delegate integration contract is not fully consistent across all delegate result shapes. In particular:
- delegate failure reports can be too sparse for the wrapper's evidence model
- wrapper summaries may hide the delegate's explicit error behind generic evidence-gate failures
- the end-to-end reviewed path would be more reliable with a normalized delegate report schema on every exit path

Recommended revisions:
1. Make delegate JSON schema consistent for all exits, including discovery failure and Excel write failure.
2. Ensure every delegate report includes at least:
   - `status`
   - `total_files`
   - `status_counter`
   - `dry_run`
   - `excel_written`
   - `output_exists`
   - `output_size_bytes`
   - `ocr_runtime_status`
   - `notes`
   - `next_steps`
   - `error` when applicable
3. Have the wrapper surface delegate `error` directly in `limitations`/`next_steps` when present.
4. Optionally document the shared report schema explicitly so wrapper/delegate compatibility is deliberate rather than inferred.
