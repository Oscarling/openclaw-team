#!/bin/zsh
# shellcheck shell=bash
#
# Provider profile helpers for local onboarding runs.
# Usage (recommended):
#   source scripts/provider_profiles.sh
#   use_deepseek_profile
#   use_gemini_profile
#   use_qwen_profile

set -euo pipefail

_provider_profile_usage() {
  cat <<'USAGE'
Usage:
  source scripts/provider_profiles.sh
  use_deepseek_profile [key_file] [model_name]
  use_gemini_profile   [key_file] [model_name]
  use_qwen_profile     [key_file] [model_name]

Optional direct execution:
  zsh scripts/provider_profiles.sh deepseek [key_file] [model_name]
  zsh scripts/provider_profiles.sh gemini   [key_file] [model_name]
  zsh scripts/provider_profiles.sh qwen     [key_file] [model_name]
USAGE
}

_provider_profile_read_text() {
  local key_file="$1"
  if [[ ! -f "$key_file" ]]; then
    return 1
  fi
  if [[ "${key_file:l}" == *.rtf ]]; then
    textutil -convert txt -stdout "$key_file" 2>/dev/null || cat "$key_file"
    return 0
  fi
  cat "$key_file"
}

_provider_profile_extract_first() {
  local key_file="$1"
  local key_regex="$2"
  _provider_profile_read_text "$key_file" \
    | tr -d '\r' \
    | sed -n "s/.*\(${key_regex}\).*/\1/p" \
    | head -n 1
}

_provider_profile_mask_tail() {
  local raw_key="$1"
  if [[ -z "$raw_key" ]]; then
    echo "(missing)"
    return 0
  fi
  local tail="${raw_key[-6,-1]}"
  echo "***${tail}"
}

_provider_profile_export_or_fail() {
  local key_value="$1"
  local key_file="$2"
  local profile_name="$3"
  if [[ -z "$key_value" ]]; then
    echo "[$profile_name] failed to extract API key from: $key_file" >&2
    return 1
  fi
  export OPENAI_API_KEY="$key_value"
  return 0
}

_provider_profile_print_active() {
  local profile_name="$1"
  echo "[$profile_name] OPENAI_API_BASE=$OPENAI_API_BASE"
  echo "[$profile_name] OPENAI_MODEL_NAME=$OPENAI_MODEL_NAME"
  echo "[$profile_name] ARGUS_LLM_WIRE_API=$ARGUS_LLM_WIRE_API"
  echo "[$profile_name] OPENAI_API_KEY=$(_provider_profile_mask_tail "$OPENAI_API_KEY")"
}

use_deepseek_profile() {
  local key_file="${1:-$HOME/Desktop/备用key/备用key-deepseek.rtf}"
  local model_name="${2:-deepseek-chat}"
  local key_value
  key_value="$(_provider_profile_extract_first "$key_file" 'sk-[A-Za-z0-9_-][A-Za-z0-9_-]*' || true)"

  _provider_profile_export_or_fail "$key_value" "$key_file" "deepseek"
  export OPENAI_API_BASE="https://api.deepseek.com"
  export OPENAI_MODEL_NAME="$model_name"
  export ARGUS_LLM_WIRE_API="chat_completions"
  _provider_profile_print_active "deepseek"
}

use_gemini_profile() {
  local key_file="${1:-$HOME/Desktop/备用key/备用key4-gemini.rtf}"
  local model_name="${2:-gemini-2.5-flash}"
  local key_value
  key_value="$(_provider_profile_extract_first "$key_file" 'AIza[A-Za-z0-9_-][A-Za-z0-9_-]*' || true)"

  _provider_profile_export_or_fail "$key_value" "$key_file" "gemini"
  export OPENAI_API_BASE="https://generativelanguage.googleapis.com/v1beta/openai"
  export OPENAI_MODEL_NAME="$model_name"
  export ARGUS_LLM_WIRE_API="chat_completions"
  _provider_profile_print_active "gemini"
}

use_qwen_profile() {
  local key_file="${1:-$HOME/Desktop/备用key/备用key6-千问.rtf}"
  local model_name="${2:-qwen-plus}"
  local key_value
  key_value="$(_provider_profile_extract_first "$key_file" 'sk-[A-Za-z0-9_-][A-Za-z0-9_-]*' || true)"

  _provider_profile_export_or_fail "$key_value" "$key_file" "qwen"
  export OPENAI_API_BASE="https://dashscope.aliyuncs.com/compatible-mode/v1"
  export OPENAI_MODEL_NAME="$model_name"
  export ARGUS_LLM_WIRE_API="chat_completions"
  _provider_profile_print_active "qwen"
}

if [[ "${ZSH_EVAL_CONTEXT:-}" == "toplevel" ]]; then
  profile="${1:-}"
  case "$profile" in
    deepseek)
      use_deepseek_profile "${2:-}" "${3:-}"
      ;;
    gemini)
      use_gemini_profile "${2:-}" "${3:-}"
      ;;
    qwen)
      use_qwen_profile "${2:-}" "${3:-}"
      ;;
    *)
      _provider_profile_usage
      exit 2
      ;;
  esac
fi
