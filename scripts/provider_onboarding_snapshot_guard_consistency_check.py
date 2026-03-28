#!/usr/bin/env python3
"""Fail-closed consistency check between snapshot guard report and history summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check snapshot guard report vs summary consistency")
    parser.add_argument(
        "--summary-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Summary json path",
    )
    parser.add_argument(
        "--guard-report-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json",
        help="Snapshot guard report json path",
    )
    return parser.parse_args()


def load_json_object(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be object: {path}")
    return data


def _build_expected_mismatch_reason_counts(report_reason_counts: Dict[str, Any]) -> Dict[str, int]:
    mapping = {
        "guard_mismatch_status": "status",
        "guard_mismatch_block_reason": "block_reason",
        "guard_mismatch_http_code_counts": "http_code_counts",
    }
    out: Dict[str, int] = {}
    for source_key, target_key in mapping.items():
        raw = report_reason_counts.get(source_key)
        if isinstance(raw, int) and raw > 0:
            out[target_key] = raw
    return dict(sorted(out.items()))


def compare_summary_vs_guard_report(summary: Dict[str, Any], report: Dict[str, Any]) -> List[str]:
    expected = {
        "assess_entry_count": report.get("evaluated_assess_rows"),
        "assess_rows_with_snapshot_guard_match": report.get("guard_match_rows"),
        "assess_rows_with_snapshot_guard_mismatch": report.get("guard_mismatch_rows"),
        "assess_rows_with_snapshot_guard_unverified": report.get("guard_unverified_rows"),
        "assess_snapshot_guard_match_percent": report.get("guard_match_percent"),
        "assess_snapshot_guard_mismatch_reason_counts": _build_expected_mismatch_reason_counts(
            report.get("reason_counts") if isinstance(report.get("reason_counts"), dict) else {}
        ),
    }
    errors: List[str] = []
    for key, expected_value in expected.items():
        actual_value = summary.get(key)
        if actual_value != expected_value:
            errors.append(
                f"summary/report mismatch for '{key}': expected={expected_value!r} actual={actual_value!r}"
            )
    return errors


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary_json)
    report_path = Path(args.guard_report_json)

    try:
        summary = load_json_object(summary_path)
        report = load_json_object(report_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors = compare_summary_vs_guard_report(summary, report)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    print(f"snapshot guard consistency passed: summary={summary_path} report={report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
