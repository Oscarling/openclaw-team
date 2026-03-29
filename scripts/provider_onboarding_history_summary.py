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


def _normalize_http_counts(raw: Any) -> Dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for key, value in raw.items():
        if isinstance(key, str) and key.isdigit() and isinstance(value, int) and value >= 0:
            out[key] = value
    return out


def _load_json_object(path_raw: Any) -> Dict[str, Any]:
    if not isinstance(path_raw, str) or not path_raw.strip():
        return {}
    path = Path(path_raw)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _snapshot_guard_matches(entry: Dict[str, Any], snapshot_payload: Dict[str, Any]) -> bool:
    if not snapshot_payload:
        return False
    if str(entry.get("status", "")) != str(snapshot_payload.get("status", "")):
        return False
    if str(entry.get("block_reason", "")) != str(snapshot_payload.get("block_reason", "")):
        return False
    entry_http = _normalize_http_counts(entry.get("http_code_counts"))
    snapshot_http = _normalize_http_counts(snapshot_payload.get("http_code_counts"))
    if entry_http and snapshot_http and entry_http != snapshot_http:
        return False
    return True


def _snapshot_guard_mismatch_reason(entry: Dict[str, Any], snapshot_payload: Dict[str, Any]) -> str:
    if str(entry.get("status", "")) != str(snapshot_payload.get("status", "")):
        return "status"
    if str(entry.get("block_reason", "")) != str(snapshot_payload.get("block_reason", "")):
        return "block_reason"
    entry_http = _normalize_http_counts(entry.get("http_code_counts"))
    snapshot_http = _normalize_http_counts(snapshot_payload.get("http_code_counts"))
    if entry_http and snapshot_http and entry_http != snapshot_http:
        return "http_code_counts"
    return "unknown"


def filter_repo_entries(entries: List[Dict[str, Any]], repo_root: Path, repo_only: bool) -> Tuple[List[Dict[str, Any]], int]:
    if not repo_only:
        return entries, 0
    kept: List[Dict[str, Any]] = []
    dropped = 0
    for entry in entries:
        base_ok = _is_under_root(entry.get("probe_tsv"), repo_root) and _is_under_root(entry.get("assessment_json"), repo_root)
        if not base_ok:
            dropped += 1
            continue
        if str(entry.get("phase", "")) == "assess":
            snapshot_path = entry.get("assessment_snapshot_json")
            if not _is_under_root(snapshot_path, repo_root):
                dropped += 1
                continue
        kept.append(entry)
    return kept, dropped


def build_summary(entries: List[Dict[str, Any]], history_path: Path, dropped_non_repo_entries: int = 0) -> Dict[str, Any]:
    status_counter = Counter(str(e.get("status", "unknown")) for e in entries)
    reason_counter = Counter(str(e.get("block_reason", "unknown")) for e in entries)
    exit_counter = Counter(str(e.get("exit_code", "unknown")) for e in entries)
    note_counter: Counter[str] = Counter()
    rows_with_note_counts = 0
    assess_rows = 0
    assess_rows_with_snapshot = 0
    assess_rows_with_snapshot_guard_match = 0
    assess_rows_with_snapshot_guard_mismatch = 0
    assess_rows_with_snapshot_guard_unverified = 0
    snapshot_guard_mismatch_reason_counter: Counter[str] = Counter()
    for entry in entries:
        if str(entry.get("phase", "")) == "assess":
            assess_rows += 1
            snapshot_path = entry.get("assessment_snapshot_json")
            if isinstance(snapshot_path, str) and snapshot_path.strip():
                assess_rows_with_snapshot += 1
                snapshot_payload = _load_json_object(snapshot_path)
                if not snapshot_payload:
                    assess_rows_with_snapshot_guard_unverified += 1
                elif _snapshot_guard_matches(entry, snapshot_payload):
                    assess_rows_with_snapshot_guard_match += 1
                else:
                    assess_rows_with_snapshot_guard_mismatch += 1
                    snapshot_guard_mismatch_reason_counter[_snapshot_guard_mismatch_reason(entry, snapshot_payload)] += 1
        note_counts = entry.get("note_class_counts")
        if not isinstance(note_counts, dict):
            continue
        if note_counts:
            rows_with_note_counts += 1
        for key, count in note_counts.items():
            if isinstance(key, str) and isinstance(count, int) and count >= 0:
                note_counter[key] += count
    latest = entries[-1] if entries else {}
    total_rows = len(entries)
    rows_missing_note_counts = total_rows - rows_with_note_counts
    note_signal_coverage_percent = 0.0
    if total_rows > 0:
        note_signal_coverage_percent = round((rows_with_note_counts / total_rows) * 100.0, 2)
    assess_rows_missing_snapshot = assess_rows - assess_rows_with_snapshot
    assess_snapshot_coverage_percent = 0.0
    if assess_rows > 0:
        assess_snapshot_coverage_percent = round((assess_rows_with_snapshot / assess_rows) * 100.0, 2)
    assess_snapshot_guard_match_percent = 0.0
    if assess_rows_with_snapshot > 0:
        assess_snapshot_guard_match_percent = round((assess_rows_with_snapshot_guard_match / assess_rows_with_snapshot) * 100.0, 2)

    return {
        "history_jsonl": str(history_path),
        "entry_count": total_rows,
        "status_counts": dict(sorted(status_counter.items())),
        "block_reason_counts": dict(sorted(reason_counter.items())),
        "exit_code_counts": dict(sorted(exit_counter.items())),
        "note_class_counts": dict(sorted(note_counter.items())),
        "rows_with_note_class_counts": rows_with_note_counts,
        "rows_missing_note_class_counts": rows_missing_note_counts,
        "note_signal_coverage_percent": note_signal_coverage_percent,
        "assess_entry_count": assess_rows,
        "assess_rows_with_snapshot": assess_rows_with_snapshot,
        "assess_rows_missing_snapshot": assess_rows_missing_snapshot,
        "assess_snapshot_coverage_percent": assess_snapshot_coverage_percent,
        "assess_rows_with_snapshot_guard_match": assess_rows_with_snapshot_guard_match,
        "assess_rows_with_snapshot_guard_mismatch": assess_rows_with_snapshot_guard_mismatch,
        "assess_rows_with_snapshot_guard_unverified": assess_rows_with_snapshot_guard_unverified,
        "assess_snapshot_guard_match_percent": assess_snapshot_guard_match_percent,
        "assess_snapshot_guard_mismatch_reason_counts": dict(sorted(snapshot_guard_mismatch_reason_counter.items())),
        "dropped_non_repo_entries": dropped_non_repo_entries,
        "latest": {
            "timestamp": latest.get("timestamp"),
            "stamp": latest.get("stamp"),
            "status": latest.get("status"),
            "block_reason": latest.get("block_reason"),
            "exit_code": latest.get("exit_code"),
            "note_class_counts": latest.get("note_class_counts"),
            "probe_tsv": latest.get("probe_tsv"),
            "assessment_json": latest.get("assessment_json"),
            "assessment_snapshot_json": latest.get("assessment_snapshot_json"),
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
