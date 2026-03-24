# Inbox Runner Contract Propagation Report

## Objective

Propagate the `BL-20260324-021` runner hardening rules back into the source-side
preview contract so future regenerated previews can inherit those rules instead
of depending on manual artifact edits.

This phase exists because `BL-20260324-021` hardened the checked-in runner
artifact on `main`, but the adapter-side automation contract still did not tell
future generated previews about:

- reviewable `partial` outcome semantics
- repo-root delegate path resolution expectations
- reviewed-script-only delegation for readonly preview flows

## Scope

In scope:

- source-side automation contract hints
- automation constraints and acceptance criteria
- automation contract profile versioning
- direct adapter regression coverage
- baseline gate wiring for the adapter test suite

Out of scope:

- another real Trello preview generation
- another approval / execute replay
- changing `artifacts/scripts/pdf_to_excel_ocr.py`
- Git finalization
- Trello writeback / Done

## Implemented Changes

Files changed:

- `PROJECT_BACKLOG.md`
- `PROJECT_CHAT_AND_WORK_LOG.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/ci.yml`
- `adapters/local_inbox_adapter.py`
- `scripts/premerge_check.sh`
- `tests/test_local_inbox_adapter.py`

### 1. New source-side contract hints for runner honesty

`adapters/local_inbox_adapter.py` now adds explicit hints covering:

- `outcome_status_model`
- `delegate_resolution`
- `reviewed_delegate_contract`

These supplement the existing fidelity, path-portability, traceability, reuse,
and runtime-summary hints with the rules learned in `BL-20260324-021`.

### 2. Stronger constraints and acceptance criteria

The automation task now explicitly requires that:

- dry-run or zero-input behavior returns a reviewable `partial` outcome
- relative delegate resolution must not depend on `Path.cwd()`
- readonly preview flows only delegate to the reviewed repo script unless they
  fail honestly

The acceptance criteria now also require:

- reviewable `partial` semantics for dry-run and zero-input conditions
- portable relative resolution of `preferred_base_script`

### 3. Contract profile version bump

The source-side automation profile now moves from:

- `narrow_script_artifact_with_repo_reuse_and_format_fidelity`

to:

- `narrow_script_artifact_with_repo_reuse_and_reviewable_runner_contract`

This makes the new expectations visible in repo truth rather than leaving them
implicit in one hardened artifact snapshot.

### 4. Adapter coverage moved into baseline gates

`tests/test_local_inbox_adapter.py` now asserts the new contract hints and the
new automation profile, and the suite is enforced in:

- `scripts/premerge_check.sh`
- `.github/workflows/ci.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`

This closes the old gap where the adapter test existed but was not part of the
baseline merge gates.

## Verification

Commands run on 2026-03-24:

```bash
python3 -m unittest -v tests/test_local_inbox_adapter.py
python3 -m unittest -v tests/test_trello_readonly_ingress.py
python3 scripts/backlog_lint.py
python3 scripts/backlog_sync.py
bash scripts/premerge_check.sh
git diff --check
```

Observed result:

- `tests/test_local_inbox_adapter.py` passed `4/4`
- `tests/test_trello_readonly_ingress.py` passed `10/10`
- `python3 scripts/backlog_lint.py` passed
- `python3 scripts/backlog_sync.py` passed while `BL-20260324-022` was mirrored
  to issue `#37`, and passed again after closeout with no remaining `phase=now`
  actionable items requiring issue mirroring
- `bash scripts/premerge_check.sh` passed with `Warnings: 0` and `Failures: 0`,
  including the newly-gated adapter suite
- `git diff --check` passed with no whitespace or patch-integrity problems

## Review Checkpoint Note

`plan-eng-review` was not separately run for this phase.

Reason:

- the change is deliberately narrow and source-contract focused
- no execution architecture, approval routing, or finalization behavior changed
- the main risk was contract drift, which is better addressed here with direct
  adapter tests plus pre-merge diff review

Pre-merge review checkpoint outcome:

- in-session diff review found no blocking structural issues in the contract
  propagation, baseline gate wiring, or backlog transition

## Remaining Risk

This phase improves what future generated previews are asked to do. It does not
prove that a future governed execute will definitely pass Critic.

The next governed validation phase still needs to create or replay preview
evidence under the updated contract and record the real result truthfully.

## Conclusion

`BL-20260324-022` is complete as a source-side contract propagation phase:

- future generated previews are now instructed to preserve the runner honesty
  rules learned in `BL-20260324-021`
- the automation contract profile records the stronger runner contract
- direct adapter assertions now live in baseline local and CI gates

The next correct step is another governed validation phase that exercises a
preview candidate under this propagated source-side contract.
