# Provider Onboarding Local Runbook

## Purpose

This runbook defines the local-first command path for provider onboarding while
`BL-20260326-099` remains blocked or when new key/base inputs arrive.

## 1) Handshake Probe Only

Generate raw endpoint matrix:

```bash
python3 scripts/provider_handshake_probe.py \
  --probe-all-keys \
  --output runtime_archives/bl100/tmp/provider_handshake_probe_manual.tsv
```

Fail fast when no `2xx` exists:

```bash
python3 scripts/provider_handshake_probe.py \
  --probe-all-keys \
  --require-success \
  --output runtime_archives/bl100/tmp/provider_handshake_probe_gate.tsv
```

## 2) Assessment Only

Convert probe TSV into structured decision JSON:

```bash
python3 scripts/provider_handshake_assess.py \
  --probe-tsv runtime_archives/bl100/tmp/provider_handshake_probe_gate.tsv \
  --output-json runtime_archives/bl100/tmp/provider_handshake_assessment_gate.json
```

Fail fast when status is not `ready`:

```bash
python3 scripts/provider_handshake_assess.py \
  --probe-tsv runtime_archives/bl100/tmp/provider_handshake_probe_gate.tsv \
  --output-json runtime_archives/bl100/tmp/provider_handshake_assessment_gate.json \
  --require-ready
```

## 3) One-Shot Gate (Recommended)

Run probe + assessment in one command:

```bash
python3 scripts/provider_onboarding_gate.py \
  --probe-all-keys \
  --require-ready \
  --stamp 20260328
```

Outputs:

- probe TSV: `runtime_archives/bl100/tmp/provider_handshake_probe_gate_<stamp>.tsv`
- assessment JSON: `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_<stamp>.json`
- history JSONL: `runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl`
- history summary JSON: `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`

Optional control for tests/special runs:

- add `--no-history-summary` to skip summary refresh in that invocation
- gate default summary refresh uses repo-only evidence filtering; add
  `--no-history-summary-repo-only` only when you intentionally need to include
  non-repo paths

## 4) Decision Rule

- `ready`: at least one `2xx` handshake row exists; proceed to real prompt-shape
  probe and controlled replay.
- `blocked`: no `2xx` handshake row; keep `BL-20260326-099` blocked and archive
  evidence/report updates.

## 5) Safety Notes

- Never print full API keys in logs/reports.
- Keep masked key tails only (`***tail`).
- Preserve local-first workflow and commit only validated evidence.

## 6) History Integrity Check

Before finalizing local evidence commits, validate onboarding history structure:

```bash
python3 scripts/provider_onboarding_history_validate.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-repo-paths
```

Also verify summary snapshot consistency against history:

```bash
python3 scripts/provider_onboarding_history_consistency_check.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --repo-only
```
