# Wait-Mode Probe Script Productization Report

## Objective

Execute `BL-20260326-100`: replace ad-hoc `/tmp` probe commands with a
repo-tracked, reproducible handshake probe script for no-key wait-mode
hardening.

## Scope

In scope:

- create a reusable probe script in repository
- support Desktop key files and RTF/plaintext parsing
- write deterministic TSV evidence without exposing full key values
- validate both missing-key and key3 paths

Out of scope:

- controlled replay
- canary promotion

## Deliverable

Script:

- `scripts/provider_handshake_probe.py`

Behavior:

- probes responses endpoints using model/input payload
- masks key in output notes (`***<tail6>`)
- outputs TSV matrix for backlog/report evidence

## Validation Evidence

- missing-key validation:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_missing_key.tsv`
- key3 validation:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_key3.tsv`

Observed key3 run on 2026-03-26:

- `aixj` responses endpoints: `401`
- `fast` responses endpoints: `403` (`error code: 1010`)

## Decision

`BL-20260326-100` is **done**.

The local wait-mode probing process is now productized and reproducible in-repo,
ready for immediate rerun once a new provider/base+key is supplied.
