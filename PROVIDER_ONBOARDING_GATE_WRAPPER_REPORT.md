# Provider Onboarding Gate Wrapper Report

## Objective

Create a one-shot local gate command that runs provider handshake probe and
assessment sequentially, so blocked/ready decisions can be generated in a
single deterministic invocation.

## Scope

In scope:

- add wrapper script to execute `probe -> assess`
- preserve fail-fast semantics with `--require-ready`
- add unit tests for command chaining and exit-code propagation
- run one live gated invocation for evidence

Out of scope:

- provider remediation
- controlled replay/canary

## Deliverables

- wrapper script:
  - `scripts/provider_onboarding_gate.py`
- tests:
  - `tests/test_provider_onboarding_gate.py`
- merge gate update:
  - `scripts/premerge_check.sh`

## Validation Evidence

- live gate probe output:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv`
- live gate assessment output:
  - `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json`
- live command outcome:
  - exited with code `2` due blocked assessment (expected)

## Result

The one-shot wrapper is working and currently reports `blocked` under the
present key/base conditions.

## Decision

Wrapper hardening is complete and can be used as the default local command for
future provider onboarding attempts.
