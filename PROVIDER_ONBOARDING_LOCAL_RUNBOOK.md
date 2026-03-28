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
- immutable assessment snapshots (new runs): `runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots/`
- history summary JSON: `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
  - includes aggregated `note_class_counts` (e.g. `invalid_api_key`,
    `edge_policy_1010`, `tls_eof`) for signal-level trend tracking
  - includes note-signal coverage metrics:
    `rows_with_note_class_counts`, `rows_missing_note_class_counts`,
    `note_signal_coverage_percent`
  - includes assess-snapshot coverage metrics:
    `assess_entry_count`, `assess_rows_with_snapshot`,
    `assess_rows_missing_snapshot`, `assess_snapshot_coverage_percent`
  - includes snapshot-guard integrity metrics:
    `assess_rows_with_snapshot_guard_match`,
    `assess_rows_with_snapshot_guard_mismatch`,
    `assess_rows_with_snapshot_guard_unverified`,
    `assess_snapshot_guard_match_percent`,
    `assess_snapshot_guard_mismatch_reason_counts`

Optional control for tests/special runs:

- add `--no-history-summary` to skip summary refresh in that invocation
- gate default summary refresh uses repo-only evidence filtering; add
  `--no-history-summary-repo-only` only when you intentionally need to include
  non-repo paths
- under repo-only filtering, `assess` rows must have repo-scoped
  `assessment_snapshot_json`; otherwise they are dropped from summary counts
- `assess_rows_with_snapshot_guard_mismatch > 0` signals decision-field drift
  between a history row and its snapshot payload, usually caused by legacy
  mutable-path overwrite before snapshot hardening
- `assess_snapshot_guard_mismatch_reason_counts` identifies which decision field
  is drifting (`status`, `block_reason`, or `http_code_counts`)

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
  --require-repo-paths \
  --require-snapshot-for-assess \
  --require-existing-files
```

Also verify summary snapshot consistency against history:

```bash
python3 scripts/provider_onboarding_history_consistency_check.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --repo-only
```

If legacy history rows are missing `note_class_counts`, run conservative
backfill (guarded by status/block/http-count match):

```bash
python3 scripts/provider_onboarding_history_backfill.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --backup-jsonl /tmp/provider_onboarding_gate_history.backup.jsonl
```

If legacy `assess` rows are missing immutable snapshot pointers, run snapshot
backfill first:

```bash
python3 scripts/provider_onboarding_history_snapshot_backfill.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --backup-jsonl /tmp/provider_onboarding_gate_history.snapshot.backup.jsonl
```

To inspect remaining missing rows and their reasons:

```bash
python3 scripts/provider_onboarding_history_backfill_gaps.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --output-json runtime_archives/bl100/tmp/provider_onboarding_history_backfill_gaps.json
```

To inspect snapshot-guard mismatches with row-level reasons:

```bash
python3 scripts/provider_onboarding_snapshot_guard_report.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --output-json runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --repo-only
```

`reason_counts` and `non_match_rows` expose exact drift causes beyond summary
aggregates (for example `guard_mismatch_block_reason` on legacy rows).
