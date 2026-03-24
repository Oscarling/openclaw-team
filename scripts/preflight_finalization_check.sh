#!/usr/bin/env bash

set -euo pipefail

failures=0
warnings=0

pass() {
  printf '[PASS] %s\n' "$1"
}

warn() {
  warnings=$((warnings + 1))
  printf '[WARN] %s\n' "$1"
}

fail() {
  failures=$((failures + 1))
  printf '[FAIL] %s\n' "$1"
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
residue_registry="docs/RUNTIME_RESIDUE_REGISTRY.tsv"

if [[ -z "$repo_root" ]]; then
  echo "Not inside a git repository."
  exit 1
fi

cd "$repo_root"

preview_path="${1:-}"
current_branch="$(git branch --show-current 2>/dev/null || true)"
remote_names="$(git remote 2>/dev/null || true)"
status_output="$(git status --short)"

is_classified_residue() {
  local path="$1"
  [[ -f "$residue_registry" ]] || return 1
  awk -F '\t' 'NF >= 1 && $1 !~ /^#/ && $1 == target { found = 1 } END { exit(found ? 0 : 1) }' \
    target="$path" "$residue_registry"
}

echo "Repo root: $repo_root"
echo "Current branch: ${current_branch:-<unknown>}"

if [[ -n "$(git remote -v)" ]]; then
  pass "git remote -v is non-empty."
else
  fail "git remote -v is empty. Formal finalization runs require a configured upstream."
fi

if [[ -n "${GIT_PUSH_REMOTE:-}" ]]; then
  if printf '%s\n' "$remote_names" | grep -qx "${GIT_PUSH_REMOTE}"; then
    pass "GIT_PUSH_REMOTE=${GIT_PUSH_REMOTE} exists in git remote list."
  else
    fail "GIT_PUSH_REMOTE=${GIT_PUSH_REMOTE} is set but not present in git remote list."
  fi
else
  fail "GIT_PUSH_REMOTE is not set."
fi

if [[ -n "${GIT_PUSH_BRANCH:-}" ]]; then
  pass "GIT_PUSH_BRANCH=${GIT_PUSH_BRANCH} is set."
else
  fail "GIT_PUSH_BRANCH is not set."
fi

if [[ "${current_branch:-}" == "main" ]]; then
  fail "Current branch is main. Formal finalization should not run directly from main."
else
  pass "Current branch is not main."
fi

if [[ "${GIT_PUSH_BRANCH:-}" == "main" ]]; then
  fail "GIT_PUSH_BRANCH points to main. Use a dedicated reviewed target or automation branch."
fi

if [[ -n "${TRELLO_API_KEY:-}" ]]; then
  pass "TRELLO_API_KEY is set."
else
  fail "TRELLO_API_KEY is not set."
fi

if [[ -n "${TRELLO_API_TOKEN:-}" ]]; then
  pass "TRELLO_API_TOKEN is set."
else
  fail "TRELLO_API_TOKEN is not set."
fi

if [[ -n "${TRELLO_DONE_LIST_ID:-}" ]]; then
  pass "TRELLO_DONE_LIST_ID is set."
else
  warn "TRELLO_DONE_LIST_ID is not set. List-name resolution may be acceptable for smoke, but explicit ID is preferred."
fi

if [[ -z "$status_output" ]]; then
  pass "Working tree is clean."
else
  runtime_residue="$(printf '%s\n' "$status_output" | grep -E '(^|\s)(preview|approvals|processed)/' || true)"
  non_runtime_dirty="$(printf '%s\n' "$status_output" | grep -Ev '(^|\s)(preview|approvals|processed)/' || true)"

  if [[ -n "$runtime_residue" ]]; then
    unclassified_runtime=""
    classified_runtime=""
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      path="$(printf '%s\n' "$line" | awk '{print $NF}')"
      if is_classified_residue "$path"; then
        classified_runtime+="$line"$'\n'
      else
        unclassified_runtime+="$line"$'\n'
      fi
    done <<< "$runtime_residue"

    if [[ -n "$classified_runtime" ]]; then
      pass "Runtime residue is classified in $residue_registry."
      printf '%s' "$classified_runtime"
    fi

    if [[ -n "$unclassified_runtime" ]]; then
      fail "Unclassified runtime residue exists under preview/, approvals/, or processed/."
      printf '%s' "$unclassified_runtime"
    fi
  fi

  if [[ -n "$non_runtime_dirty" ]]; then
    fail "Working tree contains non-runtime changes. Formal finalization requires a governed tree."
    printf '%s\n' "$non_runtime_dirty"
  elif [[ -z "$runtime_residue" ]]; then
    fail "Working tree is dirty."
    printf '%s\n' "$status_output"
  fi
fi

if [[ -n "$preview_path" ]]; then
  if [[ -f "$preview_path" ]]; then
    pass "Preview file exists: $preview_path"
    if python3 - "$preview_path" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as fh:
    payload = json.load(fh)

execution = payload.get("execution") or {}
status = execution.get("status")
executed = execution.get("executed")

if status == "processed" and executed is True:
    raise SystemExit(0)

print(f"preview is not ready: execution.status={status!r}, execution.executed={executed!r}")
raise SystemExit(1)
PY
    then
      pass "Preview execution state is ready for finalization."
    else
      fail "Preview does not satisfy execution.status=processed and execution.executed=true."
    fi
  else
    fail "Preview file does not exist: $preview_path"
  fi
else
  warn "No preview path supplied. Sample-state verification was skipped."
fi

echo
echo "Warnings: $warnings"
echo "Failures: $failures"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi
