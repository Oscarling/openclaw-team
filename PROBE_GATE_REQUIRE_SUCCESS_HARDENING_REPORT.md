# Probe Gate Require-Success Hardening Report

## Objective

Execute `BL-20260327-101`: harden provider handshake probing with explicit
success gating to prevent false-ready progression when no authenticated route is
available.

## Scope

In scope:

- add `--require-success` to repo probe script
- add unit coverage for key extraction, masking, success counting, and exit
  semantics
- enforce new test in merge gate

Out of scope:

- provider-side remediation
- controlled replay / canary

## Deliverables

- script enhancement:
  - `scripts/provider_handshake_probe.py`
- unit tests:
  - `tests/test_provider_handshake_probe.py`
- merge gate wiring:
  - `scripts/premerge_check.sh`

## Validation Evidence

- unit tests:
  - `python3 -m unittest -v tests/test_provider_handshake_probe.py` (pass)
- live gate-check matrix:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_gatecheck_20260327.tsv`
- live gate-check exit behavior:
  - command exited with code `2` and message
    `No successful (2xx) probe rows detected.`

## Decision

`BL-20260327-101` is **done**.

The project now has an explicit handshake-success gate that fails fast when
provider onboarding remains unavailable.
