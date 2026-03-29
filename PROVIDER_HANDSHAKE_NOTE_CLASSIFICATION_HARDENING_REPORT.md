# Provider Handshake Note Classification Hardening Report

## Objective

Improve provider handshake blocked-cause precision by classifying note-level
signals (not only HTTP codes) in assessment output.

## Scope

In scope:

- classify note signals such as `INVALID_API_KEY`, `1010`, TLS EOF, DNS, timeout
- include `note_class_counts` in assessment JSON output
- refine mixed transport block reason selection
- extend assessment unit coverage

Out of scope:

- provider remediation
- replay/canary execution

## Deliverables

- script update:
  - `scripts/provider_handshake_assess.py`
- tests update:
  - `tests/test_provider_handshake_assess.py`
- refreshed assessment artifact:
  - `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json`

## Validation Evidence

- unit tests:
  - `python3 -m unittest -v tests/test_provider_handshake_assess.py` (pass)
- refreshed assessment output includes:
  - `note_class_counts`
  - refined `block_reason`

## Result

Current gate assessment now reports:

- `status=blocked`
- `block_reason=auth_or_access_policy_block`
- `note_class_counts={edge_policy_1010:4, invalid_api_key:4}`

## Decision

Note-level classification hardening is complete and improves diagnostic
consistency for ongoing blocked-provider analysis.
