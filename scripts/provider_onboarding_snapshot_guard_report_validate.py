#!/usr/bin/env python3
"""Validate snapshot guard report schema and integrity constraints."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
MISMATCH_REASONS = {
    "guard_mismatch_status",
    "guard_mismatch_block_reason",
    "guard_mismatch_http_code_counts",
}
UNVERIFIED_REASONS = {
    "snapshot_missing",
    "snapshot_not_found",
    "snapshot_parse_error",
    "snapshot_not_repo_scoped",
}
ALLOWED_REASON_KEYS = {"guard_match"} | MISMATCH_REASONS | UNVERIFIED_REASONS
ALLOWED_NON_MATCH_ROW_REASONS = MISMATCH_REASONS | UNVERIFIED_REASONS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate onboarding snapshot guard report")
    parser.add_argument(
        "--report-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json",
        help="Snapshot guard report json path",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --require-repo-paths checks",
    )
    parser.add_argument(
        "--require-repo-paths",
        action="store_true",
        help="Require row-level assessment paths to be absolute and under --repo-root",
    )
    return parser.parse_args()


def _is_repo_path(value: Any, repo_root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    if not path.is_absolute():
        return False
    try:
        path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except Exception:
        return False
    return True


def _as_non_negative_int(value: Any) -> int | None:
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _validate_reason_counts(value: Any) -> tuple[Dict[str, int], List[str]]:
    errors: List[str] = []
    if not isinstance(value, dict):
        return {}, ["reason_counts must be object"]
    out: Dict[str, int] = {}
    for key, raw_count in value.items():
        if not isinstance(key, str) or not key.strip():
            errors.append("reason_counts keys must be non-empty strings")
            continue
        if key not in ALLOWED_REASON_KEYS:
            errors.append(f"reason_counts['{key}'] is not an allowed reason key")
            continue
        count = _as_non_negative_int(raw_count)
        if count is None:
            errors.append(f"reason_counts['{key}'] must be non-negative integer")
            continue
        out[key] = count
    return out, errors


def validate_report(report: Dict[str, Any], repo_root: Path, require_repo_paths: bool) -> List[str]:
    errors: List[str] = []

    numeric_fields = [
        "assess_entry_count",
        "evaluated_assess_rows",
        "guard_match_rows",
        "guard_mismatch_rows",
        "guard_unverified_rows",
        "guard_skipped_rows",
    ]
    parsed: Dict[str, int] = {}
    for key in numeric_fields:
        parsed_value = _as_non_negative_int(report.get(key))
        if parsed_value is None:
            errors.append(f"{key} must be non-negative integer")
        else:
            parsed[key] = parsed_value

    guard_match_percent = report.get("guard_match_percent")
    if not isinstance(guard_match_percent, (int, float)):
        errors.append("guard_match_percent must be numeric")
    else:
        if guard_match_percent < 0 or guard_match_percent > 100:
            errors.append("guard_match_percent must be in [0, 100]")

    reason_counts, reason_errors = _validate_reason_counts(report.get("reason_counts"))
    errors.extend(reason_errors)

    non_match_rows = report.get("non_match_rows")
    if not isinstance(non_match_rows, list):
        errors.append("non_match_rows must be array")
        non_match_rows = []

    non_match_reason_counter: Counter[str] = Counter()
    history_lines: List[int] = []
    for idx, row in enumerate(non_match_rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"non_match_rows[{idx}] must be object")
            continue
        history_line = row.get("history_line")
        if not isinstance(history_line, int) or history_line <= 0:
            errors.append(f"non_match_rows[{idx}].history_line must be positive integer")
        else:
            history_lines.append(history_line)
        reason = row.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            errors.append(f"non_match_rows[{idx}].reason must be non-empty string")
        elif reason not in ALLOWED_NON_MATCH_ROW_REASONS:
            errors.append(
                f"non_match_rows[{idx}].reason must be one of {sorted(ALLOWED_NON_MATCH_ROW_REASONS)}"
            )
        else:
            non_match_reason_counter[reason] += 1
        if require_repo_paths:
            for key in ("assessment_json", "assessment_snapshot_json"):
                value = row.get(key)
                if value is None:
                    continue
                if isinstance(value, str) and value.strip() and not _is_repo_path(value, repo_root):
                    errors.append(
                        f"non_match_rows[{idx}].{key} must be absolute repo path under {repo_root}"
                    )
    if history_lines:
        if history_lines != sorted(history_lines) or len(set(history_lines)) != len(history_lines):
            errors.append("non_match_rows history_line values must be strictly increasing and unique")

    if parsed:
        evaluated = parsed["evaluated_assess_rows"]
        total_from_parts = parsed["guard_match_rows"] + parsed["guard_mismatch_rows"] + parsed["guard_unverified_rows"]
        if evaluated != total_from_parts:
            errors.append(
                "evaluated_assess_rows must equal guard_match_rows + guard_mismatch_rows + guard_unverified_rows"
            )
        if parsed["assess_entry_count"] != evaluated + parsed["guard_skipped_rows"]:
            errors.append("assess_entry_count must equal evaluated_assess_rows + guard_skipped_rows")
        expected_non_match_len = parsed["guard_mismatch_rows"] + parsed["guard_unverified_rows"]
        if len(non_match_rows) != expected_non_match_len:
            errors.append("non_match_rows length must equal guard_mismatch_rows + guard_unverified_rows")
        if sum(reason_counts.values()) != evaluated:
            errors.append("sum(reason_counts values) must equal evaluated_assess_rows")
        if reason_counts.get("guard_match", 0) != parsed["guard_match_rows"]:
            errors.append("reason_counts['guard_match'] must equal guard_match_rows")
        mismatch_reason_total = sum(reason_counts.get(key, 0) for key in MISMATCH_REASONS)
        if mismatch_reason_total != parsed["guard_mismatch_rows"]:
            errors.append("sum(mismatch reason_counts) must equal guard_mismatch_rows")
        unverified_reason_total = sum(reason_counts.get(key, 0) for key in UNVERIFIED_REASONS)
        if unverified_reason_total != parsed["guard_unverified_rows"]:
            errors.append("sum(unverified reason_counts) must equal guard_unverified_rows")
        for key in ALLOWED_NON_MATCH_ROW_REASONS:
            if reason_counts.get(key, 0) != non_match_reason_counter.get(key, 0):
                errors.append(f"reason_counts['{key}'] must equal non_match_rows reason count")
        expected_match_percent = 0.0
        if evaluated > 0:
            expected_match_percent = round((parsed["guard_match_rows"] / evaluated) * 100.0, 2)
        if isinstance(guard_match_percent, (int, float)) and float(guard_match_percent) != expected_match_percent:
            errors.append(
                f"guard_match_percent mismatch: expected {expected_match_percent} got {guard_match_percent}"
            )

    return errors


def main() -> int:
    args = parse_args()
    report_path = Path(args.report_json)
    repo_root = Path(args.repo_root)
    if not report_path.exists():
        print(f"report file not found: {report_path}", file=sys.stderr)
        return 2
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        print(f"report is not valid JSON: {report_path}", file=sys.stderr)
        return 2
    if not isinstance(report, dict):
        print(f"report JSON must be object: {report_path}", file=sys.stderr)
        return 2

    errors = validate_report(report, repo_root=repo_root, require_repo_paths=args.require_repo_paths)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    print(f"snapshot guard report validation passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
