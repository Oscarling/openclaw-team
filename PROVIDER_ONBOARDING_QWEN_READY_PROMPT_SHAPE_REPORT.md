# Provider Onboarding Qwen Ready Prompt-Shape Report

## Context

`BL-20260326-099` required a newly supplied provider/base topology to pass:

1. lightweight handshake gate (`2xx + api_like=1`), and
2. real prompt-shape probing before promotion into controlled replay validation.

On 2026-03-29, a new Qwen key (`备用key6-千问.rtf`) was introduced and validated
against DashScope OpenAI-compatible endpoints.

## Scope

- add reusable Qwen provider preset/profile wiring in local onboarding tools
- run handshake gate using Qwen preset
- run real prompt-shape probe using `dispatcher.worker_runtime.call_llm(...)`
  with a real automation task payload (`runtime_archives/bl094/runtime/automation-task.s01.json`)

## Implementation Notes

- `scripts/provider_onboarding_gate.py`
  - adds provider preset `qwen_openai`
  - default model: `qwen-plus`
  - default endpoints:
    - `https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions`
    - `https://dashscope.aliyuncs.com/compatible-mode/v1/responses`
- `scripts/provider_profiles.sh`
  - adds `use_qwen_profile` helper
  - exports:
    - `OPENAI_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1`
    - `OPENAI_MODEL_NAME=qwen-plus` (default, overridable)
    - `ARGUS_LLM_WIRE_API=chat_completions`
- `tests/test_provider_onboarding_gate.py`
  - adds preset coverage for `qwen_openai`
- `PROVIDER_ONBOARDING_LOCAL_RUNBOOK.md`
  - adds Qwen handshake probe example
  - adds Qwen one-shot gate preset example
  - adds `use_qwen_profile` usage

## Verification Snapshot (2026-03-29)

Unit validations:

- `python3 -m unittest -v tests/test_provider_onboarding_gate.py` (passed)
- `python3 -m unittest -v tests/test_provider_handshake_probe.py tests/test_provider_handshake_assess.py tests/test_provider_onboarding_gate.py` (passed)
- `zsh -n scripts/provider_profiles.sh` (passed)

Qwen handshake gate:

- command:
  - `python3 scripts/provider_onboarding_gate.py --provider-preset qwen_openai --key-file "$HOME/Desktop/备用key/备用key6-千问.rtf" --require-ready --stamp 20260329`
- outputs:
  - `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260329.tsv`
  - `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260329.json`
  - `runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json`
- result:
  - `status=ready`
  - `success_row_count=2`
  - `http_code_counts={"200":2}`

Real prompt-shape probe (Qwen, automation payload):

- outputs:
  - `runtime_archives/bl100/tmp/provider_prompt_shape_probe_qwen_20260329.tsv`
  - `runtime_archives/bl100/tmp/provider_prompt_shape_probe_qwen_20260329.json`
- summary:
  - `status=ready`
  - `row_count=4`
  - `success_row_count=4`
  - `error_class_counts={"ok":4}`
  - prompt size baseline: `prompt_chars=6505`
  - endpoint coverage:
    - chat endpoint success `2/2`
    - responses endpoint success `2/2`

## Controlled Replay Follow-Up (Same Day)

After the ready handshake/prompt-shape probes, controlled replay was attempted
on approved preview `preview-trello-69c24cd3c1a2359ddd7a1bf8-e84af65e8f1a`:

- `runtime_archives/bl100/tmp/bl100_qwen_controlled_replay_result_20260329_escalated.json`
- `runtime_archives/bl100/tmp/bl100_qwen_controlled_replay_result_20260329_responses_wire.json`
- `runtime_archives/bl100/tmp/bl100_qwen_controlled_replay_result_20260329_responses_wire_limit1200.json`

All replay attempts remained `rejected` with `http_400`. Raw response-body
inspection shows provider-side billing state:

- `code=Arrearage`
- `message=Access denied, please make sure your account is in good standing`
- archived body evidence:
  - `runtime_archives/bl100/tmp/provider_qwen_http400_body_20260329.json`

This means Qwen route capability was demonstrated at handshake/prompt-shape
level, but replay promotion is still operationally blocked by account standing.

## Same-Day Handshake Retest Update (2026-03-29)

After controlled replay stayed blocked, the same Qwen key was re-checked via
onboarding gate:

- `python3 scripts/provider_onboarding_gate.py --provider-preset qwen_openai --key-file "$HOME/Desktop/备用key/备用key6-千问.rtf" --require-ready --stamp 20260329_retest2`

Outputs:

- `runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260329_retest2.tsv`
- `runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260329_retest2.json`

Result:

- `status=blocked`
- `block_reason=provider_account_arrearage`
- `http_code_counts={"400":2}`
- `note_class_counts={"provider_account_arrearage":2}`

Both chat and responses endpoints returned account-standing denial payloads
(`Arrearage` / `overdue-payment`), indicating the latest state is no longer
handshake-ready for this key.

## Conclusion

Qwen provider/base topology reached deterministic readiness for:

- handshake gate (`2xx + api_like`)
- real prompt-shape probes on chat/responses wires

However, both controlled replay and latest handshake retest on 2026-03-29 are
blocked by provider-side arrearage (`http_400`). BL-099 should therefore remain
blocked until provider account standing is restored and handshake/replay are
re-validated.
