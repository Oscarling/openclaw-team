# Review: pdf_to_excel_ocr_inbox_runner.py

## Scope
- Primary artifact: `artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py`
- Paired artifact: `artifacts/scripts/pdf_to_excel_ocr.py`
- Review goal: audit the wrapper and reviewed delegate together for the end-to-end readonly smoke path.

## Findings
1. **Wrapper enforces a useful readonly/evidence-backed posture**
   - The runner resolves the delegate from repository-relative locations instead of reimplementing conversion logic.
   - It performs recursive PDF discovery, explicit timeout handling, dry-run short-circuiting, and structured JSON result emission.
   - Its success gate is stronger than simple exit-code checking: it requires delegate status success, at least one file, no partial/failed counts, non-dry-run, and positive XLSX attestation.
   - This aligns well with the stated contract: do not claim OCR/conversion success without evidence.

2. **Delegate is a reasonable reviewed batch extractor with best-effort semantics**
   - The delegate supports recursive PDF discovery, OCR modes (`auto|on|off`), dry-run, JSON reporting, and per-file isolation.
   - It cleanly distinguishes aggregate `success`, `partial`, and `failed` outcomes.
   - It emits structured notes/next steps when OCR dependencies are missing or files are partial/failed.
   - It avoids overstating OCR capability and reports missing runtime dependencies explicitly.

3. **Critical end-to-end contract bug: wrapper never forwards `--dry-run` to the delegate**
   - In the runner, `--dry-run` causes the wrapper itself to return partial before delegation.
   - However, if the intended behavior is delegate dry-run compatibility, the subprocess command omits `--dry-run` entirely.
   - This means wrapper-level dry-run and delegate-level dry-run semantics are not aligned; the wrapper cannot verify delegate dry-run behavior and narrows the execution path.
   - This is not catastrophic for readonly smoke, but it weakens end-to-end fidelity.

4. **More serious integration bug: wrapper prefers stdout JSON over sidecar JSON**
   - The delegate always prints JSON to stdout and can also write the same JSON to the sidecar path.
   - The wrapper chooses `stdout_json or sidecar_json or {}`.
   - Because stdout may contain truncated or contaminated JSON while the sidecar is the stronger contract artifact, preferring stdout can discard the more reliable sidecar report.
   - For a reviewable evidence-backed pipeline, sidecar JSON should usually be preferred or reconciled, not treated as lower priority than stdout scraping.

5. **Potential parsing fragility in `_extract_json_object`**
   - The wrapper attempts to recover a JSON object from arbitrary stdout by scanning brace ranges.
   - This is permissive and can succeed on an unintended substring if stdout ever contains additional brace-like content.
   - Since the delegate already supports `--report-json`, the wrapper should rely primarily on the sidecar and treat stdout parsing as fallback.

6. **Readonly boundary is mostly respected**
   - The provided Trello-oriented metadata is only carried in the wrapper request payload and not written back externally.
   - The pair appears limited to local artifact handling and local subprocess execution.
   - No Trello writeback behavior is present in the reviewed code.

7. **Delegate behavior is mostly internally coherent**
   - `discover_pdfs`, OCR runtime detection, per-file processing, and final Excel writing/reporting are consistent.
   - Aggregate status is `success` only when no file is partial/failed, which matches the wrapper's stricter gating.
   - The delegate may return aggregate `partial` even after writing an XLSX, which is appropriate for best-effort evidence-backed reporting.

8. **Minor design observations**
   - The delegate's write step can mark the final report as `failed` if Excel writing fails, even after extraction completed. This is honest and acceptable.
   - The wrapper's `_repo_root()` heuristic is acceptable for the reviewed repository layout, though somewhat implicit.
   - The wrapper's attestation merge trusts delegate-reported output booleans/sizes over filesystem observations when types match. Filesystem attestation is generally stronger and should likely remain authoritative.

## Verdict
**needs_revision**

## Rationale
The pair is close to acceptable and demonstrates strong intent around readonly, evidence-backed, non-overclaiming behavior. However, the review cannot pass because there is a meaningful end-to-end integration weakness:

- the wrapper/delegate contract is imperfect (`--dry-run` is not forwarded), and
- the wrapper prioritizes stdout JSON scraping over the explicit `--report-json` sidecar, which can lose or weaken evidence in the exact area where the pipeline is supposed to be reviewable and deterministic.

These are revision-level issues rather than total failure because the overall structure is sound, the delegate is credible, and the wrapper largely enforces honest success criteria. But the evidence handoff path should be corrected before calling the paired implementation fully passable.

### Recommended revisions
1. Prefer sidecar JSON over stdout-derived JSON when `--report-json` is supplied; use stdout parsing only as fallback.
2. Forward `--dry-run` to the delegate if the wrapper intends to preserve delegate-compatible dry-run semantics, or explicitly document that wrapper dry-run is preflight-only and not delegated.
3. Consider keeping filesystem-derived output attestation authoritative, using delegate-reported values only as supplemental evidence.
4. Tighten `_extract_json_object` usage or reduce dependence on stdout scraping altogether.
