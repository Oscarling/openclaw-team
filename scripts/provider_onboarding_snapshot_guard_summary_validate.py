#!/usr/bin/env python3
"""Validate snapshot-guard fields in onboarding summary JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ALLOWED_MISMATCH_KEYS = {"status", "block_reason", "http_code_counts"}
REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate onboarding summary snapshot-guard fields")
    parser.add_argument(
        "--summary-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Summary json path",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --require-repo-paths checks",
    )
    parser.add_argument(
        "--require-repo-paths",
        action="store_true",
        help="Require history_jsonl to resolve under --repo-root",
    )
    return parser.parse_args()


def _as_non_negative_int(value: Any) -> int | None:
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _is_repo_path(value: Any, repo_root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (repo_root / path).expanduser()
    try:
        path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except Exception:
        return False
    return True


def validate_summary(summary: Dict[str, Any], repo_root: Path | None = None, require_repo_paths: bool = False) -> List[str]:
    errors: List[str] = []
    parsed: Dict[str, int] = {}

    history_jsonl = summary.get("history_jsonl")
    if not isinstance(history_jsonl, str) or not history_jsonl.strip():
        errors.append("history_jsonl must be non-empty string")
    elif require_repo_paths:
        root = repo_root if repo_root is not None else REPO_ROOT
        if not _is_repo_path(history_jsonl, root):
            errors.append(f"history_jsonl must resolve under repo root {root}")

    numeric_fields = [
        "assess_entry_count",
        "assess_rows_with_snapshot",
        "assess_rows_with_snapshot_guard_match",
        "assess_rows_with_snapshot_guard_mismatch",
        "assess_rows_with_snapshot_guard_unverified",
    ]
    for key in numeric_fields:
        parsed_value = _as_non_negative_int(summary.get(key))
        if parsed_value is None:
            errors.append(f"{key} must be non-negative integer")
        else:
            parsed[key] = parsed_value

    mismatch_counts = summary.get("assess_snapshot_guard_mismatch_reason_counts")
    parsed_mismatch_reason_total = 0
    if not isinstance(mismatch_counts, dict):
        errors.append("assess_snapshot_guard_mismatch_reason_counts must be object")
    else:
        for key, raw_count in mismatch_counts.items():
            if key not in ALLOWED_MISMATCH_KEYS:
                errors.append(
                    f"assess_snapshot_guard_mismatch_reason_counts['{key}'] is not an allowed mismatch key"
                )
                continue
            count = _as_non_negative_int(raw_count)
            if count is None:
                errors.append(
                    f"assess_snapshot_guard_mismatch_reason_counts['{key}'] must be non-negative integer"
                )
                continue
            parsed_mismatch_reason_total += count

    match_percent = summary.get("assess_snapshot_guard_match_percent")
    if not isinstance(match_percent, (int, float)):
        errors.append("assess_snapshot_guard_match_percent must be numeric")
    elif not (0 <= float(match_percent) <= 100):
        errors.append("assess_snapshot_guard_match_percent must be in [0, 100]")

    if parsed:
        if all(key in parsed for key in numeric_fields):
            with_snapshot = parsed["assess_rows_with_snapshot"]
            if with_snapshot > parsed["assess_entry_count"]:
                errors.append("assess_rows_with_snapshot must be <= assess_entry_count")
            observed_guard_total = (
                parsed["assess_rows_with_snapshot_guard_match"]
                + parsed["assess_rows_with_snapshot_guard_mismatch"]
                + parsed["assess_rows_with_snapshot_guard_unverified"]
            )
            if observed_guard_total != with_snapshot:
                errors.append(
                    "assess_rows_with_snapshot_guard_match + assess_rows_with_snapshot_guard_mismatch + "
                    "assess_rows_with_snapshot_guard_unverified must equal assess_rows_with_snapshot"
                )
            if parsed_mismatch_reason_total != parsed["assess_rows_with_snapshot_guard_mismatch"]:
                errors.append(
                    "sum(assess_snapshot_guard_mismatch_reason_counts values) must equal "
                    "assess_rows_with_snapshot_guard_mismatch"
                )
            expected_percent = 0.0
            if with_snapshot > 0:
                expected_percent = round((parsed["assess_rows_with_snapshot_guard_match"] / with_snapshot) * 100.0, 2)
            if isinstance(match_percent, (int, float)) and float(match_percent) != expected_percent:
                errors.append(
                    f"assess_snapshot_guard_match_percent mismatch: expected {expected_percent} got {match_percent}"
                )

    return errors


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary_json)
    repo_root = Path(args.repo_root)
    if not summary_path.exists():
        print(f"summary file not found: {summary_path}", file=sys.stderr)
        return 2
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        print(f"summary is not valid JSON: {summary_path}", file=sys.stderr)
        return 2
    if not isinstance(summary, dict):
        print(f"summary JSON must be object: {summary_path}", file=sys.stderr)
        return 2

    errors = validate_summary(summary, repo_root=repo_root, require_repo_paths=args.require_repo_paths)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    print(f"snapshot guard summary validation passed: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
