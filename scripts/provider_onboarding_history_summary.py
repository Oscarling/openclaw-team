#!/usr/bin/env python3
"""Summarize provider onboarding gate history jsonl into one JSON snapshot."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


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


def build_summary(entries: List[Dict[str, Any]], history_path: Path) -> Dict[str, Any]:
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
    output_path.parent.mkdir(parents=True, exist_ok=True)

    entries = load_entries(history_path)
    summary = build_summary(entries, history_path)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
