# Endpoint-Chain Route Discovery Probe Report

## Objective

Execute the first diagnostic slice of `BL-20260326-095`: determine whether a
stable real-endpoint route exists for the automation prompt under current
provider topology.

## Scope

In scope:

- probe primary/fallback endpoints across model variants and payload styles
- isolate whether failures are size-driven, shape-driven, or endpoint-driven
- produce deterministic evidence artifacts under `runtime_archives/bl095/`

Out of scope:

- production rollback threshold clearance canary
- provider-side SLA/infra remediation

## Probe Set

1. Endpoint/model/payload matrix:
   - `runtime_archives/bl095/tmp/bl095_probe_matrix.tsv`
2. Fallback payload-size sweep (simple payload):
   - `runtime_archives/bl095/tmp/bl095_payload_sweep.tsv`
3. Real automation-prompt limit probe (actual task shape):
   - `runtime_archives/bl095/tmp/bl095_prompt_limit_probe.tsv`
4. Reliability retest on seemingly-promising setting:
   - `runtime_archives/bl095/tmp/bl095_limit1200_repeats.tsv`

## Results

Primary path (`aixj.vip`):

- all tested model/payload combinations remained `HTTP 502`
- unaffected by payload style (`ping` vs heavy inputs) or model variant

Fallback path (`fast.vpsairobot.com`):

- lightweight probes and simple payload-size sweep returned `HTTP 200`
  (including simple strings up to `4096` chars)
- but real automation prompt shape still timed out under 45s budget:
  - `/responses`: timeout across all tested compaction limits (`0/1200/800/600/400/250`)
  - `/v1/responses`: mostly timeout; one transient success appeared once in
    limit sweep but failed 4/4 in immediate reliability retest at the same setting
    (`field_limit=1200`)

## Interpretation

- blocker is not merely raw payload length or model name.
- blocker is the real automation prompt shape + endpoint runtime behavior under
  current topology.
- no stable route was found in this diagnostic slice for governed canary
  promotion thresholds.

## Decision

`BL-20260326-095` remains **blocked**.

Next blocker candidate:

- `BL-20260326-096`: establish an alternative stable provider/endpoint route
  for real automation prompt execution (or equivalent topology change) before
  re-entering governed canary clearance.
