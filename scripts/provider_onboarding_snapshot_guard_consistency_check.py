#!/usr/bin/env python3
"""Fail-closed consistency check between snapshot guard report and history summary."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report_validate.py"
SUMMARY_VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_summary_validate.py"


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
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --require-repo-paths checks",
    )
    parser.add_argument(
        "--require-repo-paths",
        action="store_true",
        help="Require report row-level paths to be absolute and under --repo-root",
    )
    return parser.parse_args()


def load_json_object(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be object: {path}")
    return data


def _load_validate_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report_validate", VALIDATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load snapshot guard report validate module from {VALIDATE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_summary_validate_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_summary_validate", SUMMARY_VALIDATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load snapshot guard summary validate module from {SUMMARY_VALIDATE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def _normalized_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return str(Path(value).expanduser().resolve(strict=False))


def compare_summary_vs_guard_report(summary: Dict[str, Any], report: Dict[str, Any]) -> List[str]:
    expected = {
        "assess_entry_count": report.get("evaluated_assess_rows"),
        "assess_rows_with_snapshot": report.get("evaluated_assess_rows"),
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
    if _normalized_path(summary.get("history_jsonl")) != _normalized_path(report.get("history_jsonl")):
        errors.append(
            "summary/report mismatch for 'history_jsonl': "
            f"expected={report.get('history_jsonl')!r} actual={summary.get('history_jsonl')!r}"
        )
    return errors


def main() -> int:
    args = parse_args()
    summary_path = Path(args.summary_json)
    report_path = Path(args.guard_report_json)
    repo_root = Path(args.repo_root)

    try:
        summary = load_json_object(summary_path)
        report = load_json_object(report_path)
        summary_validate_mod = _load_summary_validate_module()
        summary_validation_errors = summary_validate_mod.validate_summary(
            summary,
            repo_root=repo_root,
            require_repo_paths=args.require_repo_paths,
        )
        if summary_validation_errors:
            for err in summary_validation_errors:
                print(f"summary validation error: {err}", file=sys.stderr)
            return 2
        validate_mod = _load_validate_module()
        validation_errors = validate_mod.validate_report(
            report,
            repo_root=repo_root,
            require_repo_paths=args.require_repo_paths,
        )
        if validation_errors:
            for err in validation_errors:
                print(f"report validation error: {err}", file=sys.stderr)
            return 2
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
