# DeepSeek Onboarding And Controlled Replay Promotion Report

## Context

BL-20260326-099 was blocked on provider onboarding promotion after prior Qwen
route attempts ended with provider-side billing arrearage (`http_400`).

## What Changed On 2026-03-29

- Ran DeepSeek key validation against desktop backup keys under real network
  access:
  - key file: `~/Desktop/备用key/备用key-deepseek.rtf`
  - chat endpoint: `https://api.deepseek.com/v1/chat/completions` (`200`)
  - responses endpoint: `https://api.deepseek.com/v1/responses` (`404`)
  - assessment status: `ready`
- Promoted the same route through project gate:
  - `scripts/provider_onboarding_gate.py` with output dir
    `runtime_archives/bl100/tmp/deepseek_desktop`
  - history summary latest switched to `status=ready`, `block_reason=none`
- Replayed governed preview with DeepSeek profile:
  - preview: `preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a`
  - first replay after provider cutover reached critic stage (`needs_revision`)
  - after critic static-evidence policy clarification in
    `skills/execute_approved_previews.py`, rerun reached
    `status=processed`, `critic_verdict=pass`

## Mainline Outcome

- BL-20260326-099 done criteria are satisfied:
  - new provider/base topology onboarded
  - handshake/prompt-shape gate is `ready`
  - governed controlled replay promotion reached `processed`

## Key Evidence

- `runtime_archives/bl100/tmp/deepseek_desktop/provider_handshake_probe_gate_20260329.tsv`
- `runtime_archives/bl100/tmp/deepseek_desktop/provider_handshake_assessment_gate_20260329.json`
- `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
- `preview/preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a.json`
- `approvals/preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a.result.json`

## Validation

- `python3 -m unittest -v tests/test_execute_approved_previews.py`
- `python3 -m unittest -v tests/test_project_delivery_status.py tests/test_project_delivery_signal.py tests/test_project_delivery_signal_bundle.py tests/test_project_delivery_signal_consistency_check.py`
- `python3 scripts/project_delivery_status.py --backlog PROJECT_BACKLOG.md --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json --repo-root /Users/lingguozhong/openclaw-team`

All checks above passed in this session.
