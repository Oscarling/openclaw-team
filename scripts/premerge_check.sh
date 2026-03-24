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

current_branch="$(git branch --show-current 2>/dev/null || true)"
status_output="$(git status --short)"

is_classified_residue() {
  local path="$1"
  [[ -f "$residue_registry" ]] || return 1
  awk -F '\t' 'NF >= 1 && $1 !~ /^#/ && $1 == target { found = 1 } END { exit(found ? 0 : 1) }' \
    target="$path" "$residue_registry"
}

echo "Repo root: $repo_root"
echo "Current branch: ${current_branch:-<unknown>}"

if [[ "${current_branch:-}" == "main" ]]; then
  fail "Current branch is main. Create a topic branch before merge-ready validation."
else
  pass "Current branch is not main."
fi

if git ls-files --error-unmatch PROJECT_CHAT_AND_WORK_LOG.md >/dev/null 2>&1; then
  pass "PROJECT_CHAT_AND_WORK_LOG.md is tracked."
elif [[ -f PROJECT_CHAT_AND_WORK_LOG.md ]]; then
  warn "PROJECT_CHAT_AND_WORK_LOG.md exists but is not tracked. Track it before formal phase closeout."
else
  warn "PROJECT_CHAT_AND_WORK_LOG.md is missing. Confirm another current-state ledger is in force."
fi

if git ls-files --error-unmatch PROJECT_BACKLOG.md >/dev/null 2>&1; then
  pass "PROJECT_BACKLOG.md is tracked."
elif [[ -f PROJECT_BACKLOG.md ]]; then
  warn "PROJECT_BACKLOG.md exists but is not tracked. Track it before merge-ready validation."
else
  fail "PROJECT_BACKLOG.md is missing. Backlog sweep cannot be verified."
fi

if python3 scripts/backlog_lint.py; then
  pass "PROJECT_BACKLOG.md passes backlog lint."
else
  fail "PROJECT_BACKLOG.md backlog lint failed."
fi

runtime_residue="$(printf '%s\n' "$status_output" | grep -E '(^|\s)(preview|approvals|processed)/' || true)"
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
    pass "All listed runtime residue is classified in $residue_registry."
    printf '%s' "$classified_runtime"
  fi

  if [[ -n "$unclassified_runtime" ]]; then
    fail "Unclassified runtime residue exists under preview/, approvals/, or processed/."
    printf '%s' "$unclassified_runtime"
  fi
else
  pass "No runtime residue detected under preview/, approvals/, or processed/."
fi

if bash -n scripts/preflight_finalization_check.sh; then
  pass "preflight_finalization_check.sh syntax is valid."
else
  fail "preflight_finalization_check.sh syntax check failed."
fi

echo
echo "Running baseline unit tests..."
if python3 -m unittest -v tests/test_backlog_lint.py; then
  pass "tests/test_backlog_lint.py passed."
else
  fail "tests/test_backlog_lint.py failed."
fi

if python3 -m unittest -v tests/test_argus_hardening.py; then
  pass "tests/test_argus_hardening.py passed."
else
  fail "tests/test_argus_hardening.py failed."
fi

if python3 -m unittest -v tests/test_processed_finalization.py; then
  pass "tests/test_processed_finalization.py passed."
else
  fail "tests/test_processed_finalization.py failed."
fi

echo
echo "Warnings: $warnings"
echo "Failures: $failures"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi
