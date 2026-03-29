#!/usr/bin/env python3
"""Fail-closed consistency check between history and persisted snapshot guard report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report.py"
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report_validate.py"
SUMMARY_CONSISTENCY_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_consistency_check.py"
SUMMARY_VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_summary_validate.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check snapshot guard report consistency with history")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="Input history jsonl path",
    )
    parser.add_argument(
        "--report-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json",
        help="Snapshot guard report json path to verify",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --repo-only filtering",
    )
    parser.add_argument(
        "--repo-only",
        action="store_true",
        help="Apply repo-only filtering while recomputing expected report",
    )
    parser.add_argument(
        "--summary-json",
        default="",
        help="Optional summary json path. When set, enforce summary/report consistency on the same report.",
    )
    parser.add_argument(
        "--require-repo-paths",
        action="store_true",
        help="Validate report row paths as absolute repo-scoped paths before comparing",
    )
    return parser.parse_args()


def _load_report_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report", REPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load report module from {REPORT_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_validate_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report_validate", VALIDATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load report validate module from {VALIDATE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_summary_consistency_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_consistency_check", SUMMARY_CONSISTENCY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load summary consistency module from {SUMMARY_CONSISTENCY_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_summary_validate_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_summary_validate", SUMMARY_VALIDATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load summary validate module from {SUMMARY_VALIDATE_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_expected_report(history_path: Path, repo_root: Path, repo_only: bool) -> Dict[str, Any]:
    mod = _load_report_module()
    rows = mod.load_history(history_path)
    return mod.build_snapshot_guard_report(rows, history_path=history_path, repo_root=repo_root, repo_only=repo_only)


def load_report_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"report file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("report JSON must be an object")
    return data


def _normalized_path(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    return str(Path(value).expanduser().resolve(strict=False))


def compare_report(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    keys_to_compare = [
        "repo_only",
        "assess_entry_count",
        "evaluated_assess_rows",
        "guard_match_rows",
        "guard_mismatch_rows",
        "guard_unverified_rows",
        "guard_skipped_rows",
        "guard_match_percent",
        "reason_counts",
        "non_match_rows",
    ]
    errors: List[str] = []
    for key in keys_to_compare:
        if actual.get(key) != expected.get(key):
            errors.append(f"report mismatch for '{key}': expected={expected.get(key)!r} actual={actual.get(key)!r}")
    if _normalized_path(actual.get("history_jsonl")) != _normalized_path(expected.get("history_jsonl")):
        errors.append(
            "report mismatch for 'history_jsonl': "
            f"expected={expected.get('history_jsonl')!r} actual={actual.get('history_jsonl')!r}"
        )
    return errors


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    report_path = Path(args.report_json)
    repo_root = Path(args.repo_root)
    summary_path = Path(args.summary_json) if args.summary_json else None

    try:
        validate_mod = _load_validate_module()
        actual = load_report_json(report_path)
        validation_errors = validate_mod.validate_report(
            actual,
            repo_root=repo_root,
            require_repo_paths=args.require_repo_paths,
        )
        if validation_errors:
            for err in validation_errors:
                print(f"report validation error: {err}", file=sys.stderr)
            return 2
        expected = build_expected_report(history_path=history_path, repo_root=repo_root, repo_only=args.repo_only)
        if summary_path is not None:
            summary_mod = _load_summary_consistency_module()
            summary_validate_mod = _load_summary_validate_module()
            summary = summary_mod.load_json_object(summary_path)
            summary_validation_errors = summary_validate_mod.validate_summary(
                summary,
                repo_root=repo_root,
                require_repo_paths=args.require_repo_paths,
            )
            if summary_validation_errors:
                for err in summary_validation_errors:
                    print(f"summary validation error: {err}", file=sys.stderr)
                return 2
            summary_errors = summary_mod.compare_summary_vs_guard_report(summary, actual)
            if summary_errors:
                for err in summary_errors:
                    print(f"summary/report mismatch: {err}", file=sys.stderr)
                return 2
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors = compare_report(expected, actual)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    print(f"snapshot guard report consistency passed: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
