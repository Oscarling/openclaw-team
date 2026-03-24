# Preview Artifact Contract Hardening Report

## Scope

This report covers the source-side contract hardening that follows
[TRELLO_LIVE_PREVIEW_EXECUTION_REPORT.md](/Users/lingguozhong/openclaw-team/TRELLO_LIVE_PREVIEW_EXECUTION_REPORT.md).

Goal:

- reduce the chance that the next generated inbox runner repeats the same
  `needs_revision` findings
- harden the adapter-side task contract rather than patching one runtime artifact
  by hand
- keep this phase limited to contract code and tests

Out of scope:

- another live preview creation run
- another approval / execute run
- git finalization
- Trello Done / writeback

## Findings Addressed

The prior governed execute surfaced four artifact-quality concerns:

- output path ended with `.xlsx`, but the generated script wrote non-XLSX text
  content
- input path was hardcoded instead of staying parameter-driven
- automation description context collapsed to `Purpose:`
- review lacked stronger contract guidance about runtime-summary expectations

## Implemented Changes

Files changed:

- [adapters/local_inbox_adapter.py](/Users/lingguozhong/openclaw-team/adapters/local_inbox_adapter.py)
- [tests/test_local_inbox_adapter.py](/Users/lingguozhong/openclaw-team/tests/test_local_inbox_adapter.py)

### 1. Better automation description condensation

Changed `_condense_automation_description(...)` so it now:

- strips zero-width / non-breaking whitespace artifacts
- keeps multiple meaningful lines before the `Execution contract:` suffix
- joins those lines into one compact traceable summary
- avoids collapsing long structured descriptions down to a heading fragment such
  as `Purpose:`

### 2. Stronger automation reuse contract

The PDF-to-Excel automation task now includes explicit source hints:

- `preferred_base_script = artifacts/scripts/pdf_to_excel_ocr.py`
- `reference_docs` pointing to:
  - `artifacts/docs/pdf_to_excel_ocr_usage.md`
  - `artifacts/reviews/pdf_to_excel_ocr_review.md`

Interpretation:

- future automation is now steered toward wrapping or adapting the existing
  repository script that already has true XLSX semantics evidence, instead of
  improvising a brand-new implementation from scratch

### 3. Stronger fidelity and portability rules

Added explicit `contract_hints`, constraints, and acceptance criteria covering:

- true `.xlsx` fidelity:
  do not write XML / CSV / plaintext to a `.xlsx` path
- path portability:
  do not hardcode the input directory when `input_dir` is already provided in
  params
- traceability:
  preserve meaningful description context instead of collapsing it to a heading
  fragment
- runtime summary expectation:
  generated script should emit a structured summary for later reviewability

### 4. Contract profile versioning

Updated automation metadata profile from:

- `narrow_script_artifact`

to:

- `narrow_script_artifact_with_repo_reuse_and_format_fidelity`

This makes the hardened contract visible in repo truth rather than leaving it as
an unversioned prompt nuance.

## Gstack Checkpoint Decision

Explicit skip rationale:

- no extra gstack skill was used beyond standard pre-merge review discipline
- this phase is a narrow adapter contract hardening plus tests, not a new
  architecture or live-system investigation

## Local Verification

Commands run:

```bash
python3 -m unittest -v tests/test_local_inbox_adapter.py
python3 -m unittest -v tests/test_trello_readonly_ingress.py
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
bash scripts/premerge_check.sh
```

Observed result:

- local inbox adapter tests passed `2/2`
- Trello read-only ingress tests passed `8/8`
- backlog lint passed
- backlog sync passed with no remaining `phase=now` actionable items requiring
  mirrored issues
- `premerge_check.sh` passed with `Warnings: 0` and `Failures: 0`

## Remaining Gap

This phase hardens the source contract only. It does not retroactively change the
already-executed preview from the prior phase.

Why:

- existing preview internal tasks are already frozen in
  [preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de.json](/Users/lingguozhong/openclaw-team/preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-354139fc92de.json)
- the current dedupe freeze still prevents simply creating a new preview from the
  same Trello origin without an explicit rerun path

So the next validation step must be a new governed phase:

- either obtain a fresh live card / preview candidate
- or define an explicit regeneration path for validating the hardened contract

## Conclusion

`BL-20260324-018` is complete as a source-side hardening phase:

- meaningful description context is preserved better
- future automation is steered toward the existing repo script
- output-format fidelity and path-portability rules are now explicit contract
  requirements
- repository tests lock these expectations in

The next step is not another silent retry. The next step is a separate governed
validation phase that exercises the hardened contract on a fresh preview candidate.
