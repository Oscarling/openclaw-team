#!/usr/bin/env python3
"""Report onboarding snapshot guard mismatches with row-level reasons."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Report onboarding snapshot guard details")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path",
    )
    parser.add_argument(
        "--output-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_snapshot_guard_report.json",
        help="Output report JSON path",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --repo-only filtering",
    )
    parser.add_argument(
        "--repo-only",
        action="store_true",
        help="When set, require assess evidence paths to stay under --repo-root",
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


def _is_under_root(value: Any, root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        path = Path(value).expanduser().resolve(strict=False)
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
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def classify_guard_row(entry: Dict[str, Any], repo_root: Path, repo_only: bool) -> Tuple[str, Dict[str, Any]]:
    if str(entry.get("phase", "")) != "assess":
        return "skip_non_assess", {}

    probe_tsv = entry.get("probe_tsv")
    assessment_json = entry.get("assessment_json")
    snapshot_json = entry.get("assessment_snapshot_json")

    if repo_only:
        if not _is_under_root(probe_tsv, repo_root) or not _is_under_root(assessment_json, repo_root):
            return "skip_non_repo_base_paths", {}
        if not _is_under_root(snapshot_json, repo_root):
            return "snapshot_not_repo_scoped", {"assessment_snapshot_json": snapshot_json}

    if not isinstance(snapshot_json, str) or not snapshot_json.strip():
        return "snapshot_missing", {"assessment_snapshot_json": snapshot_json}

    snapshot_path = Path(snapshot_json)
    if not snapshot_path.exists():
        return "snapshot_not_found", {"assessment_snapshot_json": snapshot_json}

    snapshot_payload = _load_json_object(snapshot_json)
    if not snapshot_payload:
        return "snapshot_parse_error", {"assessment_snapshot_json": snapshot_json}

    entry_status = str(entry.get("status", ""))
    snap_status = str(snapshot_payload.get("status", ""))
    if entry_status != snap_status:
        return "guard_mismatch_status", {"entry_status": entry_status, "snapshot_status": snap_status}

    entry_reason = str(entry.get("block_reason", ""))
    snap_reason = str(snapshot_payload.get("block_reason", ""))
    if entry_reason != snap_reason:
        return "guard_mismatch_block_reason", {"entry_block_reason": entry_reason, "snapshot_block_reason": snap_reason}

    entry_http = _normalize_http_counts(entry.get("http_code_counts"))
    snap_http = _normalize_http_counts(snapshot_payload.get("http_code_counts"))
    if entry_http and snap_http and entry_http != snap_http:
        return "guard_mismatch_http_code_counts", {"entry_http_code_counts": entry_http, "snapshot_http_code_counts": snap_http}

    return "guard_match", {}


def build_snapshot_guard_report(history_rows: List[Dict[str, Any]], history_path: Path, repo_root: Path, repo_only: bool) -> Dict[str, Any]:
    assess_rows = 0
    match_rows = 0
    mismatch_rows = 0
    unverified_rows = 0
    skipped_rows = 0
    reason_counter: Counter[str] = Counter()
    non_match_rows: List[Dict[str, Any]] = []

    mismatch_reasons = {
        "guard_mismatch_status",
        "guard_mismatch_block_reason",
        "guard_mismatch_http_code_counts",
    }
    unverified_reasons = {
        "snapshot_missing",
        "snapshot_not_found",
        "snapshot_parse_error",
        "snapshot_not_repo_scoped",
    }

    for idx, row in enumerate(history_rows, start=1):
        reason, detail = classify_guard_row(row, repo_root=repo_root, repo_only=repo_only)
        if reason == "skip_non_assess":
            continue
        assess_rows += 1
        if reason.startswith("skip_"):
            skipped_rows += 1
            continue
        reason_counter[reason] += 1
        if reason == "guard_match":
            match_rows += 1
            continue
        if reason in mismatch_reasons:
            mismatch_rows += 1
        elif reason in unverified_reasons:
            unverified_rows += 1
        non_match_rows.append(
            {
                "history_line": idx,
                "timestamp": row.get("timestamp"),
                "stamp": row.get("stamp"),
                "status": row.get("status"),
                "block_reason": row.get("block_reason"),
                "assessment_json": row.get("assessment_json"),
                "assessment_snapshot_json": row.get("assessment_snapshot_json"),
                "reason": reason,
                "detail": detail,
            }
        )

    guard_match_percent = 0.0
    evaluated_rows = match_rows + mismatch_rows + unverified_rows
    if evaluated_rows > 0:
        guard_match_percent = round((match_rows / evaluated_rows) * 100.0, 2)

    return {
        "history_jsonl": str(history_path),
        "repo_only": bool(repo_only),
        "assess_entry_count": assess_rows,
        "evaluated_assess_rows": evaluated_rows,
        "guard_match_rows": match_rows,
        "guard_mismatch_rows": mismatch_rows,
        "guard_unverified_rows": unverified_rows,
        "guard_skipped_rows": skipped_rows,
        "guard_match_percent": guard_match_percent,
        "reason_counts": dict(sorted(reason_counter.items())),
        "non_match_rows": non_match_rows,
    }


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    output_path = Path(args.output_json)
    repo_root = Path(args.repo_root)
    rows = load_history(history_path)
    report = build_snapshot_guard_report(rows, history_path=history_path, repo_root=repo_root, repo_only=args.repo_only)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
