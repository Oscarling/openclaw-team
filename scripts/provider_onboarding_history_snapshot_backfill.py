#!/usr/bin/env python3
"""Backfill immutable assessment_snapshot_json pointers for onboarding history."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill assessment_snapshot_json in onboarding history jsonl")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path to update",
    )
    parser.add_argument(
        "--snapshot-dir",
        default="runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots",
        help="Directory for immutable snapshot files",
    )
    parser.add_argument(
        "--backup-jsonl",
        default="",
        help="Optional backup path (defaults to <history>.bak when omitted)",
    )
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit non-zero when assess rows without assessment_snapshot_json remain after backfill",
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


def write_history(path: Path, entries: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(entry, ensure_ascii=False) for entry in entries]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _normalize_assessment_payload(payload: Any) -> Optional[Dict[str, Any]]:
    return payload if isinstance(payload, dict) else None


def load_assessment_payload(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return _normalize_assessment_payload(parsed)


def _compact_timestamp(raw: Any) -> str:
    if not isinstance(raw, str) or not raw.strip():
        return "unknown_time"
    try:
        return datetime.fromisoformat(raw).strftime("%Y%m%dT%H%M%S")
    except ValueError:
        return raw.replace(":", "").replace("-", "").replace(" ", "_")


def build_snapshot_path(snapshot_dir: Path, entry: Dict[str, Any], line_no: int) -> Path:
    stamp = entry.get("stamp")
    stamp_str = str(stamp) if isinstance(stamp, str) and stamp else "unknown_stamp"
    time_key = _compact_timestamp(entry.get("timestamp"))
    return snapshot_dir / f"provider_handshake_assessment_gate_{stamp_str}_{time_key}_line{line_no}.json"


def backfill_snapshot_entries(
    entries: List[Dict[str, Any]],
    snapshot_dir: Path,
    dry_run: bool,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    updated: List[Dict[str, Any]] = []
    stats = {
        "entry_count": len(entries),
        "already_present": 0,
        "normalized_existing": 0,
        "backfilled": 0,
        "skipped_non_assess": 0,
        "skipped_missing_assessment_path": 0,
        "skipped_assessment_not_found": 0,
        "skipped_assessment_unreadable": 0,
    }

    for idx, row in enumerate(entries, start=1):
        next_row = dict(row)
        phase = str(next_row.get("phase", ""))
        if phase != "assess":
            stats["skipped_non_assess"] += 1
            updated.append(next_row)
            continue

        existing_snapshot = next_row.get("assessment_snapshot_json")
        if isinstance(existing_snapshot, str) and existing_snapshot.strip():
            snapshot_path = Path(existing_snapshot)
            if not snapshot_path.is_absolute():
                snapshot_path = REPO_ROOT / snapshot_path
            if snapshot_path.exists():
                resolved_snapshot = str(snapshot_path.resolve())
                if next_row.get("assessment_snapshot_json") != resolved_snapshot:
                    next_row["assessment_snapshot_json"] = resolved_snapshot
                    stats["normalized_existing"] += 1
                stats["already_present"] += 1
                updated.append(next_row)
                continue

        assess_path_raw = next_row.get("assessment_json")
        if not isinstance(assess_path_raw, str) or not assess_path_raw.strip():
            stats["skipped_missing_assessment_path"] += 1
            updated.append(next_row)
            continue

        assess_path = Path(assess_path_raw)
        if not assess_path.is_absolute():
            assess_path = REPO_ROOT / assess_path
        if not assess_path.exists():
            stats["skipped_assessment_not_found"] += 1
            updated.append(next_row)
            continue

        payload = load_assessment_payload(assess_path)
        if payload is None:
            stats["skipped_assessment_unreadable"] += 1
            updated.append(next_row)
            continue

        target = build_snapshot_path(snapshot_dir, next_row, idx)
        next_row["assessment_snapshot_json"] = str(target.resolve())
        if not dry_run:
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stats["backfilled"] += 1
        updated.append(next_row)

    return updated, stats


def count_assess_missing_snapshot(entries: List[Dict[str, Any]]) -> int:
    remaining = 0
    for row in entries:
        if str(row.get("phase", "")) != "assess":
            continue
        snapshot = row.get("assessment_snapshot_json")
        if not isinstance(snapshot, str) or not snapshot.strip():
            remaining += 1
    return remaining


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    if not history_path.is_absolute():
        history_path = REPO_ROOT / history_path
    snapshot_dir = Path(args.snapshot_dir)
    if not snapshot_dir.is_absolute():
        snapshot_dir = REPO_ROOT / snapshot_dir
    entries = load_history(history_path)
    updated, stats = backfill_snapshot_entries(entries, snapshot_dir=snapshot_dir, dry_run=args.dry_run)

    backup_path = Path(args.backup_jsonl) if args.backup_jsonl else Path(str(history_path) + ".bak")
    if not args.dry_run:
        if history_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_text(history_path.read_text(encoding="utf-8"), encoding="utf-8")
        write_history(history_path, updated)

    remaining_missing = count_assess_missing_snapshot(updated)
    stats["remaining_missing_snapshot_for_assess"] = remaining_missing

    result = {
        "history_jsonl": str(history_path),
        "snapshot_dir": str(snapshot_dir),
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
