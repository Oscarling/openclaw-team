# Provider Handshake Assessment Automation Report

## Objective

Automate post-probe decisioning while `BL-20260326-099` remains blocked, so the
project can deterministically classify provider readiness (`ready` vs `blocked`)
without manual matrix inspection.

## Scope

In scope:

- add a repo script that parses handshake TSV matrices and emits JSON summary
- classify dominant block reason from HTTP code mix
- support fail-fast gate (`--require-ready`) for local/CI usage
- add unit coverage and include tests in premerge checks

Out of scope:

- provider remediation
- real prompt-shape probe execution

## Deliverables

- assessment script:
  - `scripts/provider_handshake_assess.py`
- unit tests:
  - `tests/test_provider_handshake_assess.py`
- gate integration:
  - `scripts/premerge_check.sh`

## Validation Evidence

- assessed matrix:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_retest_allkeys_20260327b.tsv`
- generated summary:
  - `runtime_archives/bl100/tmp/provider_handshake_assessment_20260328.json`
- gate-check behavior:
  - `python3 scripts/provider_handshake_assess.py --probe-tsv ... --require-ready`
    exits with code `2` and reason `auth_or_access_policy_block`

## Result

Automated assessment output confirms:

- `status=blocked`
- `block_reason=auth_or_access_policy_block`
- `http_code_counts={401:4, 403:4}`
- `success_row_count=0`

## Decision

This automation hardening is complete and can be reused in every future
provider retest cycle.
