# Provider Route Retest Report (2026-03-27)

## Objective

Re-verify whether previously saved Desktop key/base combinations became usable on
2026-03-27 before advancing beyond the provider onboarding gate.

## Scope

In scope:

- retest all discovered key candidates from Desktop backup files
- probe both `aixj` and `fast` responses endpoints
- produce reproducible matrix evidence

Out of scope:

- real prompt-shape execution
- controlled replay and canary promotion

## Evidence

- retest matrix:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_retest_allkeys_20260327b.tsv`

## Results

Observed key tails:

- `***c0352c`
- `***J86gzy`

Observed endpoint results:

- `https://aixj.vip/{v1/}responses` -> `401 INVALID_API_KEY`
- `https://fast.vpsairobot.com/{v1/}responses` -> `403` (`error code: 1010`)

No `2xx` success row was observed.

## Decision

Provider onboarding remains blocked as of 2026-03-27.

## Next Action Gate

- keep BL-099 blocked until a new key/base combination reaches authenticated
  handshake success (`2xx`), then proceed to real prompt-shape probe.
