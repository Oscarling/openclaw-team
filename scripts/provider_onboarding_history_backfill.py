#!/usr/bin/env python3
"""Conservatively backfill note_class_counts into onboarding history jsonl."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill note_class_counts in onboarding history jsonl")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path to update",
    )
    parser.add_argument(
        "--backup-jsonl",
        default="",
        help="Optional backup path (defaults to <history>.bak when omitted)",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit non-zero when rows without note_class_counts remain after backfill",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute backfill result without writing files",
    )
    return parser.parse_args()


def load_history(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def load_assessment(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _normalize_counts(raw: Any) -> Dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for k, v in raw.items():
        if isinstance(k, str) and k and isinstance(v, int) and v >= 0:
            out[k] = v
    return out


def _can_backfill(entry: Dict[str, Any], assess: Dict[str, Any]) -> bool:
    # Conservative guard: only backfill when key decision fields still match.
    if not assess:
        return False
    if str(entry.get("status", "")) != str(assess.get("status", "")):
        return False
    if str(entry.get("block_reason", "")) != str(assess.get("block_reason", "")):
        return False

    entry_http = entry.get("http_code_counts")
    assess_http = assess.get("http_code_counts")
    if isinstance(entry_http, dict) and isinstance(assess_http, dict):
        if entry_http != assess_http:
            return False
    return True


def backfill_entries(entries: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    updated: List[Dict[str, Any]] = []
    stats = {
        "entry_count": len(entries),
        "already_present": 0,
        "backfilled": 0,
        "skipped_no_assessment": 0,
        "skipped_guard_mismatch": 0,
        "skipped_no_note_counts": 0,
    }
    for row in entries:
        next_row = dict(row)
        existing = next_row.get("note_class_counts")
        if isinstance(existing, dict):
            stats["already_present"] += 1
            updated.append(next_row)
            continue

        assessment_path_raw = next_row.get("assessment_snapshot_json") or next_row.get("assessment_json")
        assessment_path = Path(str(assessment_path_raw)) if assessment_path_raw else Path("")
        if not assessment_path_raw or not assessment_path.exists():
            stats["skipped_no_assessment"] += 1
            updated.append(next_row)
            continue

        assess = load_assessment(assessment_path)
        if not _can_backfill(next_row, assess):
            stats["skipped_guard_mismatch"] += 1
            updated.append(next_row)
            continue

        note_counts = _normalize_counts(assess.get("note_class_counts"))
        if not note_counts:
            stats["skipped_no_note_counts"] += 1
            updated.append(next_row)
            continue

        next_row["note_class_counts"] = note_counts
        stats["backfilled"] += 1
        updated.append(next_row)

    return updated, stats


def write_history(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, ensure_ascii=False) for entry in entries]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    entries = load_history(history_path)
    updated, stats = backfill_entries(entries)

    backup_path = Path(args.backup_jsonl) if args.backup_jsonl else Path(str(history_path) + ".bak")
    if not args.dry_run:
        if history_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(history_path.read_text(encoding="utf-8"), encoding="utf-8")
        write_history(history_path, updated)

    remaining_missing = 0
    for row in updated:
        if not isinstance(row.get("note_class_counts"), dict):
            remaining_missing += 1
    stats["remaining_missing_note_counts"] = remaining_missing

    result = {
        "history_jsonl": str(history_path),
        "backup_jsonl": str(backup_path),
        "dry_run": bool(args.dry_run),
        **stats,
    }
    print(json.dumps(result, ensure_ascii=False))
    if args.require_complete and remaining_missing > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
