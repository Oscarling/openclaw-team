#!/usr/bin/env python3
"""Fail-closed consistency check between onboarding history jsonl and summary json."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_history_summary.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check onboarding history summary consistency")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="Input history jsonl path",
    )
    parser.add_argument(
        "--summary-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Summary json path to verify",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --repo-only filtering",
    )
    parser.add_argument(
        "--repo-only",
        action="store_true",
        help="Apply repo-only filtering while recomputing expected summary",
    )
    return parser.parse_args()


def _load_summary_module():
    spec = importlib.util.spec_from_file_location("provider_onboarding_history_summary", SUMMARY_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load summary module from {SUMMARY_SCRIPT}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_expected_summary(history_path: Path, repo_root: Path, repo_only: bool) -> Dict[str, Any]:
    mod = _load_summary_module()
    entries = mod.load_entries(history_path)
    filtered_entries, dropped_non_repo_entries = mod.filter_repo_entries(entries, repo_root, repo_only)
    return mod.build_summary(filtered_entries, history_path, dropped_non_repo_entries=dropped_non_repo_entries)


def load_summary_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"summary file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("summary JSON must be an object")
    return data


def compare_summary(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[str]:
    keys_to_compare = [
        "entry_count",
        "status_counts",
        "block_reason_counts",
        "exit_code_counts",
        "dropped_non_repo_entries",
        "latest",
    ]
    errors: List[str] = []
    for key in keys_to_compare:
        if actual.get(key) != expected.get(key):
            errors.append(
                f"summary mismatch for '{key}': expected={expected.get(key)!r} actual={actual.get(key)!r}"
            )
    return errors


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    summary_path = Path(args.summary_json)
    repo_root = Path(args.repo_root)

    try:
        expected = build_expected_summary(history_path, repo_root, args.repo_only)
        actual = load_summary_json(summary_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors = compare_summary(expected, actual)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2

    print(f"history-summary consistency passed: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
