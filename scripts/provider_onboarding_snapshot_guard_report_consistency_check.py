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
    return parser.parse_args()


def _load_report_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report", REPORT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load report module from {REPORT_SCRIPT}")
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
    return errors


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    report_path = Path(args.report_json)
    repo_root = Path(args.repo_root)

    try:
        expected = build_expected_report(history_path=history_path, repo_root=repo_root, repo_only=args.repo_only)
        actual = load_report_json(report_path)
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
