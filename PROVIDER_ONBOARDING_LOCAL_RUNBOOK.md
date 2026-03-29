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

Probe command now defaults to `--retry-attempts 2` for retryable transport/5xx
failures. Use `--retry-attempts 1` to disable retries in strict single-shot mode.
Generated TSV now includes retry observability columns:
`retry_count` and `retry_reasons`.

Fail fast when no `2xx` exists:

```bash
python3 scripts/provider_handshake_probe.py \
  --probe-all-keys \
  --require-success \
  --output runtime_archives/bl100/tmp/provider_handshake_probe_gate.tsv
```

Gemini (OpenAI compatibility) example:

```bash
python3 scripts/provider_handshake_probe.py \
  --key-file "$HOME/Desktop/备用key/备用key4-gemini.rtf" \
  --endpoint "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" \
  --model "gemini-3-flash-preview" \
  --output runtime_archives/bl100/tmp/provider_handshake_probe_gemini.tsv
```

`--key-file` also supports passing a directory path (for example
`$HOME/Desktop/备用key/`); probe will scan text/rtf files inside and extract
candidate keys.

Qwen (DashScope OpenAI compatibility) example:

```bash
python3 scripts/provider_handshake_probe.py \
  --key-file "$HOME/Desktop/备用key/备用key6-千问.rtf" \
  --endpoint "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  --endpoint "https://dashscope.aliyuncs.com/compatible-mode/v1/responses" \
  --model "qwen-plus" \
  --output runtime_archives/bl100/tmp/provider_handshake_probe_qwen.tsv
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

Gemini preset shortcut (uses preset default endpoint/model):

```bash
python3 scripts/provider_onboarding_gate.py \
  --provider-preset gemini_openai \
  --key-file "$HOME/Desktop/备用key/备用key4-gemini.rtf" \
  --require-ready \
  --stamp 20260328
```

Qwen preset shortcut (uses DashScope compatible endpoints):

```bash
python3 scripts/provider_onboarding_gate.py \
  --provider-preset qwen_openai \
  --key-file "$HOME/Desktop/备用key/备用key6-千问.rtf" \
  --require-ready \
  --stamp 20260329
```

`--stamp` must be a valid `YYYYMMDD` date (for example `20260329`). Do not add
suffixes like `_retest`; repeated same-day runs should reuse the same stamp and
be distinguished by per-run `timestamp` and immutable assessment snapshots in
history.

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

- `ready`: at least one handshake row is both `2xx` and `api_like=1` (real API
  payload), then proceed to real prompt-shape probe and controlled replay.
- `blocked`: no `2xx + api_like=1` row; keep `BL-20260326-099` blocked and
  archive evidence/report updates.

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

To enforce summary/report snapshot-guard metric consistency:

```bash
python3 scripts/provider_onboarding_snapshot_guard_consistency_check.py \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --guard-report-json runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-repo-paths
```

To validate snapshot-guard report schema/path integrity:

```bash
python3 scripts/provider_onboarding_snapshot_guard_report_validate.py \
  --report-json runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-repo-paths
```

To ensure persisted snapshot-guard report is fresh against history:

```bash
python3 scripts/provider_onboarding_snapshot_guard_report_consistency_check.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --report-json runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --repo-only \
  --require-repo-paths
```

To validate persisted snapshot-guard report schema/path integrity:

```bash
python3 scripts/provider_onboarding_snapshot_guard_report_validate.py \
  --report-json runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-repo-paths
```

To validate snapshot-guard summary schema integrity:

```bash
python3 scripts/provider_onboarding_snapshot_guard_summary_validate.py \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-repo-paths
```

## 7) Non-Technical Delivery Status Board

To generate a concise project-level status board (completion %, critical blocked
chain BL-092~BL-099, onboarding latest state, and recommended next step):

```bash
python3 scripts/project_delivery_status.py \
  --backlog PROJECT_BACKLOG.md \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --output-json runtime_archives/bl100/tmp/project_delivery_status.json \
  --output-md runtime_archives/bl100/tmp/project_delivery_status.md
```

Use this output for operator-facing progress updates when BL-099 remains
blocked and external provider/base readiness is still pending.

Status JSON also includes `blocking_signal` for quick machine/operator triage:

- `stage`:
  - `handshake_gate` when onboarding latest itself is blocked
  - `controlled_replay_promotion` when handshake is ready but BL-099 promotion
    is still blocked by downstream external conditions
  - `provider_chain`/`unknown` for residual chain-level blocking
- `reason`:
  - mirrors the most actionable blocker reason (for example
    `provider_account_arrearage`, `auth_or_access_policy_block`,
    `provider_billing_arrearage`)

For one-shot artifact generation (recommended), produce both signal outputs
and run embedded consistency checks in a single command:

```bash
python3 scripts/project_delivery_signal_bundle.py \
  --status-json runtime_archives/bl100/tmp/project_delivery_status.json \
  --output-prefix /tmp/project_delivery_status.signal \
  --require-delivery-state \
  --require-blocking-context \
  --output-summary-json /tmp/project_delivery_status.signal.bundle.summary.json
```

This writes:

- `/tmp/project_delivery_status.signal.json`
- `/tmp/project_delivery_status.signal.tsv`
- `/tmp/project_delivery_status.signal.bundle.summary.json`

For compact extraction only (no bundling), use:

```bash
python3 scripts/project_delivery_signal.py \
  --status-json runtime_archives/bl100/tmp/project_delivery_status.json \
  --output-format tsv
```

Strict extraction mode requires:

- `--require-delivery-state`
- `--require-blocking-context`

In strict mode, non-ready `delivery_state` must include both
`blocking_stage` and `blocking_reason`.

To verify signal artifacts remain consistent with source status JSON:

```bash
python3 scripts/project_delivery_signal_consistency_check.py \
  --status-json runtime_archives/bl100/tmp/project_delivery_status.json \
  --signal-json /tmp/project_delivery_status.signal.json \
  --signal-tsv /tmp/project_delivery_status.signal.tsv
```

For fail-fast readiness gating (automation use), add `--require-ready`; command
returns exit code `2` unless `delivery_state=ready_for_replay`:

```bash
python3 scripts/project_delivery_status.py \
  --backlog PROJECT_BACKLOG.md \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root /Users/lingguozhong/openclaw-team \
  --require-ready
```

## 8) Provider Environment Profile Shortcuts

When switching between provider baselines during local debugging, use the
repo-tracked helper instead of ad-hoc `/tmp` snippets:

```bash
source scripts/provider_profiles.sh
```

DeepSeek profile (OpenAI-compatible chat wire):

```bash
use_deepseek_profile
```

Gemini profile (OpenAI compatibility route):

```bash
use_gemini_profile
```

Qwen profile (DashScope OpenAI compatibility route):

```bash
use_qwen_profile
```

Both helpers export:

- `OPENAI_API_BASE`
- `OPENAI_MODEL_NAME`
- `ARGUS_LLM_WIRE_API=chat_completions`
- `OPENAI_API_KEY` (extracted from Desktop key file, never printed in full)

Optional overrides:

```bash
use_deepseek_profile "$HOME/Desktop/备用key/custom-deepseek.rtf" "deepseek-chat"
use_gemini_profile "$HOME/Desktop/备用key/custom-gemini.rtf" "gemini-2.5-flash"
use_qwen_profile "$HOME/Desktop/备用key/custom-qwen.rtf" "qwen-plus"
```
