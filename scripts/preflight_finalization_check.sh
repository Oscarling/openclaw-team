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
allowed_candidate_paths=""

is_classified_residue() {
  local path="$1"
  [[ -f "$residue_registry" ]] || return 1
  awk -F '\t' 'NF >= 1 && $1 !~ /^#/ && $1 == target { found = 1 } END { exit(found ? 0 : 1) }' \
    target="$path" "$residue_registry"
}

is_allowed_candidate_path() {
  local path="$1"
  [[ -n "$allowed_candidate_paths" ]] || return 1
  printf '%s\n' "$allowed_candidate_paths" | grep -Fxq "$path"
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

if [[ -n "$preview_path" && -f "$preview_path" ]]; then
  allowed_candidate_paths="$(python3 - "$preview_path" <<'PY'
import sys
from pathlib import Path

from skills.finalize_processed_previews import REPO_ROOT, _collect_commit_paths, load_json

raw = Path(sys.argv[1])
preview_path = raw if raw.is_absolute() else (REPO_ROOT / raw)
preview_path = preview_path.resolve()
payload = load_json(preview_path)
paths = _collect_commit_paths(preview_path, payload, REPO_ROOT)
print("\n".join(paths))
PY
)"
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
    allowed_candidate_dirty=""
    unexpected_non_runtime_dirty=""
    while IFS= read -r line; do
      [[ -n "$line" ]] || continue
      path="$(printf '%s\n' "$line" | awk '{print $NF}')"
      if is_allowed_candidate_path "$path"; then
        allowed_candidate_dirty+="$line"$'\n'
      else
        unexpected_non_runtime_dirty+="$line"$'\n'
      fi
    done <<< "$non_runtime_dirty"

    if [[ -n "$allowed_candidate_dirty" ]]; then
      pass "Dirty non-runtime files match the supplied preview candidate set."
      printf '%s' "$allowed_candidate_dirty"
    fi

    if [[ -n "$unexpected_non_runtime_dirty" ]]; then
      fail "Working tree contains non-runtime changes outside the supplied preview candidate set."
      printf '%s' "$unexpected_non_runtime_dirty"
    fi
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
