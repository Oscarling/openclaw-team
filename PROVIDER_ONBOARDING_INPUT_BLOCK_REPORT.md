# Provider Onboarding Input Block Report

## Objective

Record the current unblock status for `BL-20260326-099` while operating in
local-first mode without a newly usable provider/base+key topology.

## Scope

In scope:

- verify whether Desktop `备用key3` can pass route handshake probes
- archive objective evidence for backlog state transition
- keep project continuity explicit for interrupted sessions

Out of scope:

- full controlled replay
- canary promotion window

## Evidence

- key3 handshake probe matrix:
  - `runtime_archives/bl099/tmp/bl099_key3_probe_matrix.tsv`

## Results (2026-03-26)

Probe setup:

- model: `gpt-5-codex`
- payload: `input=ping`
- endpoints:
  - `https://aixj.vip/v1/responses`
  - `https://aixj.vip/responses`
  - `https://fast.vpsairobot.com/v1/responses`
  - `https://fast.vpsairobot.com/responses`

Observed outcome:

- all endpoints returned `401 INVALID_API_KEY`
- no endpoint reached authenticated handshake success (`200`)

## Decision

`BL-20260326-099` is **blocked** until a newly usable provider/base+key
combination is supplied.

## Next Action Gate

- once a new provider/base+key is available, run handshake probe first, then
  run real prompt-shape probe before controlled replay.
