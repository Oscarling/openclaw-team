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

if python3 scripts/backlog_sync.py; then
  pass "PROJECT_BACKLOG.md passes issue mirror sync checks."
else
  fail "PROJECT_BACKLOG.md issue mirror sync failed."
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

if python3 -m unittest -v tests/test_backlog_sync.py; then
  pass "tests/test_backlog_sync.py passed."
else
  fail "tests/test_backlog_sync.py failed."
fi

if python3 -m unittest -v tests/test_pin_trello_done_list.py; then
  pass "tests/test_pin_trello_done_list.py passed."
else
  fail "tests/test_pin_trello_done_list.py failed."
fi

if python3 -m unittest -v tests/test_trello_readonly_ingress.py; then
  pass "tests/test_trello_readonly_ingress.py passed."
else
  fail "tests/test_trello_readonly_ingress.py failed."
fi

if python3 -m unittest -v tests/test_local_inbox_adapter.py; then
  pass "tests/test_local_inbox_adapter.py passed."
else
  fail "tests/test_local_inbox_adapter.py failed."
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

if python3 -m unittest -v tests/test_pdf_to_excel_ocr_inbox_runner.py; then
  pass "tests/test_pdf_to_excel_ocr_inbox_runner.py passed."
else
  fail "tests/test_pdf_to_excel_ocr_inbox_runner.py failed."
fi

if python3 -m unittest -v tests/test_execute_approved_previews.py; then
  pass "tests/test_execute_approved_previews.py passed."
else
  fail "tests/test_execute_approved_previews.py failed."
fi

if python3 -m unittest -v tests/test_provider_handshake_probe.py; then
  pass "tests/test_provider_handshake_probe.py passed."
else
  fail "tests/test_provider_handshake_probe.py failed."
fi

if python3 -m unittest -v tests/test_provider_handshake_assess.py; then
  pass "tests/test_provider_handshake_assess.py passed."
else
  fail "tests/test_provider_handshake_assess.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_gate.py; then
  pass "tests/test_provider_onboarding_gate.py passed."
else
  fail "tests/test_provider_onboarding_gate.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_summary.py; then
  pass "tests/test_provider_onboarding_history_summary.py passed."
else
  fail "tests/test_provider_onboarding_history_summary.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_validate.py; then
  pass "tests/test_provider_onboarding_history_validate.py passed."
else
  fail "tests/test_provider_onboarding_history_validate.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_consistency_check.py; then
  pass "tests/test_provider_onboarding_history_consistency_check.py passed."
else
  fail "tests/test_provider_onboarding_history_consistency_check.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_backfill.py; then
  pass "tests/test_provider_onboarding_history_backfill.py passed."
else
  fail "tests/test_provider_onboarding_history_backfill.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_snapshot_backfill.py; then
  pass "tests/test_provider_onboarding_history_snapshot_backfill.py passed."
else
  fail "tests/test_provider_onboarding_history_snapshot_backfill.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_history_backfill_gaps.py; then
  pass "tests/test_provider_onboarding_history_backfill_gaps.py passed."
else
  fail "tests/test_provider_onboarding_history_backfill_gaps.py failed."
fi

if python3 -m unittest -v tests/test_provider_onboarding_snapshot_guard_report.py; then
  pass "tests/test_provider_onboarding_snapshot_guard_report.py passed."
else
  fail "tests/test_provider_onboarding_snapshot_guard_report.py failed."
fi

if python3 scripts/provider_onboarding_history_backfill.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --dry-run; then
  pass "provider onboarding history backfill dry-run check passed."
else
  fail "provider onboarding history backfill dry-run check failed."
fi

if python3 scripts/provider_onboarding_history_snapshot_backfill.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --dry-run; then
  pass "provider onboarding history snapshot backfill dry-run check passed."
else
  fail "provider onboarding history snapshot backfill dry-run check failed."
fi

if python3 scripts/provider_onboarding_history_backfill_gaps.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --output-json /tmp/provider_onboarding_history_backfill_gaps_premerge.json; then
  pass "provider onboarding history backfill gaps report check passed."
else
  fail "provider onboarding history backfill gaps report check failed."
fi

if python3 scripts/provider_onboarding_snapshot_guard_report.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --output-json /tmp/provider_onboarding_snapshot_guard_report_premerge.json \
  --repo-root "$repo_root" \
  --repo-only; then
  pass "provider onboarding snapshot guard report check passed."
else
  fail "provider onboarding snapshot guard report check failed."
fi

if python3 scripts/provider_onboarding_history_validate.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --repo-root "$repo_root" \
  --require-repo-paths \
  --require-snapshot-for-assess \
  --require-existing-files; then
  pass "provider onboarding gate history jsonl passes schema/path validation."
else
  fail "provider onboarding gate history jsonl validation failed."
fi

if python3 scripts/provider_onboarding_history_consistency_check.py \
  --history-jsonl runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl \
  --summary-json runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json \
  --repo-root "$repo_root" \
  --repo-only; then
  pass "provider onboarding history summary is consistent with history jsonl."
else
  fail "provider onboarding history summary consistency check failed."
fi

echo
echo "Warnings: $warnings"
echo "Failures: $failures"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi
