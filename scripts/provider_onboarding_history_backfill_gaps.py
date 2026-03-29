#!/usr/bin/env python3
"""Report remaining onboarding history rows missing note_class_counts with reasons."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report onboarding history backfill gaps")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path",
    )
    parser.add_argument(
        "--output-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_history_backfill_gaps.json",
        help="Output report JSON path",
    )
    return parser.parse_args()


def load_history(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
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


def _normalize_note_counts(raw: Any) -> Dict[str, int]:
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, int] = {}
    for key, value in raw.items():
        if isinstance(key, str) and key and isinstance(value, int) and value >= 0:
            out[key] = value
    return out


def classify_gap(entry: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    source_field = "assessment_snapshot_json" if entry.get("assessment_snapshot_json") else "assessment_json"
    assessment_path_raw = entry.get(source_field)
    if not assessment_path_raw:
        return "assessment_missing", {"detail": "assessment path missing", "source_field": source_field}

    assess_path = Path(str(assessment_path_raw))
    if not assess_path.exists():
        return "assessment_missing", {"detail": "assessment path not found", "source_field": source_field}

    assess = load_assessment(assess_path)
    if not assess:
        return "assessment_parse_error", {"detail": "assessment json unreadable", "source_field": source_field}

    entry_status = str(entry.get("status", ""))
    assess_status = str(assess.get("status", ""))
    if entry_status != assess_status:
        return "guard_mismatch_status", {
            "entry_status": entry_status,
            "assessment_status": assess_status,
            "source_field": source_field,
        }

    entry_reason = str(entry.get("block_reason", ""))
    assess_reason = str(assess.get("block_reason", ""))
    if entry_reason != assess_reason:
        return "guard_mismatch_block_reason", {
            "entry_block_reason": entry_reason,
            "assessment_block_reason": assess_reason,
            "source_field": source_field,
        }

    entry_http = entry.get("http_code_counts")
    assess_http = assess.get("http_code_counts")
    if isinstance(entry_http, dict) and isinstance(assess_http, dict) and entry_http != assess_http:
        return "guard_mismatch_http_code_counts", {
            "entry_http_code_counts": entry_http,
            "assessment_http_code_counts": assess_http,
            "source_field": source_field,
        }

    note_counts = _normalize_note_counts(assess.get("note_class_counts"))
    if not note_counts:
        return "assessment_note_counts_missing", {"detail": "assessment note_class_counts missing/invalid", "source_field": source_field}

    return "backfillable_now", {"assessment_note_class_counts": note_counts, "source_field": source_field}


def build_gap_report(history_rows: List[Dict[str, Any]], history_path: Path) -> Dict[str, Any]:
    missing_rows: List[Dict[str, Any]] = []
    reason_counter: Counter[str] = Counter()

    for idx, row in enumerate(history_rows, start=1):
        if isinstance(row.get("note_class_counts"), dict):
            continue
        reason, detail = classify_gap(row)
        reason_counter[reason] += 1
        missing_rows.append(
            {
                "history_line": idx,
                "timestamp": row.get("timestamp"),
                "stamp": row.get("stamp"),
                "status": row.get("status"),
                "block_reason": row.get("block_reason"),
                "assessment_json": row.get("assessment_json"),
                "reason": reason,
                "detail": detail,
            }
        )

    return {
        "history_jsonl": str(history_path),
        "entry_count": len(history_rows),
        "missing_note_count_rows": len(missing_rows),
        "reason_counts": dict(sorted(reason_counter.items())),
        "missing_rows": missing_rows,
    }


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    output_path = Path(args.output_json)
    rows = load_history(history_path)
    report = build_gap_report(rows, history_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
