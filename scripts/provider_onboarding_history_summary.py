#!/usr/bin/env python3
"""Summarize provider onboarding gate history jsonl into one JSON snapshot."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize provider onboarding gate history")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="Input history jsonl path",
    )
    parser.add_argument(
        "--output-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Output summary json path",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root used by --repo-only filtering",
    )
    parser.add_argument(
        "--repo-only",
        action="store_true",
        help="Count only entries whose evidence paths are under --repo-root",
    )
    return parser.parse_args()


def load_entries(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    entries: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                entries.append(obj)
        except Exception:
            continue
    return entries


def _is_under_root(value: Any, root: Path) -> bool:
    if not value:
        return False
    try:
        path = Path(str(value)).expanduser().resolve(strict=False)
        path.relative_to(root.resolve(strict=False))
        return True
    except Exception:
        return False


def filter_repo_entries(entries: List[Dict[str, Any]], repo_root: Path, repo_only: bool) -> Tuple[List[Dict[str, Any]], int]:
    if not repo_only:
        return entries, 0
    kept: List[Dict[str, Any]] = []
    dropped = 0
    for entry in entries:
        if _is_under_root(entry.get("probe_tsv"), repo_root) and _is_under_root(entry.get("assessment_json"), repo_root):
            kept.append(entry)
        else:
            dropped += 1
    return kept, dropped


def build_summary(entries: List[Dict[str, Any]], history_path: Path, dropped_non_repo_entries: int = 0) -> Dict[str, Any]:
    status_counter = Counter(str(e.get("status", "unknown")) for e in entries)
    reason_counter = Counter(str(e.get("block_reason", "unknown")) for e in entries)
    exit_counter = Counter(str(e.get("exit_code", "unknown")) for e in entries)
    latest = entries[-1] if entries else {}

    return {
        "history_jsonl": str(history_path),
        "entry_count": len(entries),
        "status_counts": dict(sorted(status_counter.items())),
        "block_reason_counts": dict(sorted(reason_counter.items())),
        "exit_code_counts": dict(sorted(exit_counter.items())),
        "dropped_non_repo_entries": dropped_non_repo_entries,
        "latest": {
            "timestamp": latest.get("timestamp"),
            "stamp": latest.get("stamp"),
            "status": latest.get("status"),
            "block_reason": latest.get("block_reason"),
            "exit_code": latest.get("exit_code"),
            "probe_tsv": latest.get("probe_tsv"),
            "assessment_json": latest.get("assessment_json"),
        },
    }


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    output_path = Path(args.output_json)
    repo_root = Path(args.repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    entries = load_entries(history_path)
    filtered_entries, dropped_non_repo_entries = filter_repo_entries(entries, repo_root, args.repo_only)
    summary = build_summary(filtered_entries, history_path, dropped_non_repo_entries=dropped_non_repo_entries)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
