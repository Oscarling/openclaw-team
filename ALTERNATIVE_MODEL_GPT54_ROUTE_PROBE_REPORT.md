# Alternative Model GPT-5.4 Route Probe Report

## Objective

Execute the first candidate experiment for `BL-20260326-097`: test whether
switching to `gpt-5.4` on the fast provider can recover real automation prompt
execution stability.

## Scope

In scope:

- verify lightweight availability for `gpt-5.4`
- run real automation prompt-shape probes on both fast endpoints
- evaluate prompt-compaction limits against 45s timeout budget

Out of scope:

- full canary promotion window
- provider-side performance tuning

## Evidence

- lightweight availability check (`gpt-5.4`, input=`ping`) on:
  - `https://fast.vpsairobot.com/responses`
  - `https://fast.vpsairobot.com/v1/responses`
- real prompt-shape probe matrix:
  - `runtime_archives/bl097/tmp/bl097_prompt_limit_probe_gpt54.tsv`

## Results

Lightweight availability:

- both fast endpoints returned `200` for `ping`.

Real prompt-shape behavior:

- `/responses`: all tested limits (`0/1200/800/600/400/250`) failed
  (`timeout` dominant, one `tls_eof`).
- `/v1/responses`: all tested limits failed (`timeout`).
- no successful completion for the captured real automation prompt shape under
  current 45s probe budget.

## Decision

`BL-20260326-097` is **not cleared**.

Current status:

- model switch to `gpt-5.4` did not recover route stability for real prompt
  shape.

Next blocker candidate:

- `BL-20260326-098`: provision and validate a genuinely alternative
  provider/endpoint route (new base/key topology) before re-entering canary
  clearance.
