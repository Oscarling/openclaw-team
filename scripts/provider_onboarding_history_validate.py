#!/usr/bin/env python3
"""Validate provider onboarding gate history jsonl structure and field quality."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
STAMP_RE = re.compile(r"^\d{8}$")
ALLOWED_PHASES = {"probe", "assess"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate provider onboarding gate history jsonl")
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path to validate",
    )
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repo root for --require-repo-paths checks",
    )
    parser.add_argument(
        "--require-repo-paths",
        action="store_true",
        help="Require probe_tsv/assessment_json paths to be absolute and under --repo-root",
    )
    parser.add_argument(
        "--require-snapshot-for-assess",
        action="store_true",
        help="Require assess-phase rows to include assessment_snapshot_json",
    )
    parser.add_argument(
        "--require-existing-files",
        action="store_true",
        help="Require referenced probe/assessment/snapshot files to exist on disk",
    )
    return parser.parse_args()


def _is_repo_path(value: Any, repo_root: Path) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    path = Path(value)
    if not path.is_absolute():
        return False
    try:
        path.resolve(strict=False).relative_to(repo_root.resolve(strict=False))
    except Exception:
        return False
    return True


def _path_exists(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return Path(value).exists()


def validate_entry(
    entry: Dict[str, Any],
    line_no: int,
    repo_root: Path,
    require_repo_paths: bool,
    require_snapshot_for_assess: bool = False,
    require_existing_files: bool = False,
) -> List[str]:
    errors: List[str] = []

    timestamp = entry.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp.strip():
        errors.append(f"line {line_no}: missing/invalid timestamp")
    else:
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            errors.append(f"line {line_no}: timestamp is not ISO-8601")

    stamp = entry.get("stamp")
    if not isinstance(stamp, str) or not STAMP_RE.match(stamp):
        errors.append(f"line {line_no}: stamp must be YYYYMMDD string")

    phase = entry.get("phase")
    if phase not in ALLOWED_PHASES:
        errors.append(f"line {line_no}: phase must be one of {sorted(ALLOWED_PHASES)}")

    status = entry.get("status")
    if not isinstance(status, str) or not status.strip():
        errors.append(f"line {line_no}: missing/invalid status")

    block_reason = entry.get("block_reason")
    if not isinstance(block_reason, str) or not block_reason.strip():
        errors.append(f"line {line_no}: missing/invalid block_reason")

    exit_code = entry.get("exit_code")
    if not isinstance(exit_code, int) or exit_code < 0:
        errors.append(f"line {line_no}: exit_code must be non-negative integer")

    if require_repo_paths:
        for key in ("probe_tsv", "assessment_json"):
            if not _is_repo_path(entry.get(key), repo_root):
                errors.append(f"line {line_no}: {key} must be absolute repo path under {repo_root}")
    if require_existing_files:
        for key in ("probe_tsv", "assessment_json"):
            if not _path_exists(entry.get(key)):
                errors.append(f"line {line_no}: {key} path not found")

    snapshot_path = entry.get("assessment_snapshot_json")
    if require_snapshot_for_assess and phase == "assess":
        if not isinstance(snapshot_path, str) or not snapshot_path.strip():
            errors.append(f"line {line_no}: assessment_snapshot_json required for assess phase")
    if snapshot_path is not None and snapshot_path != "":
        if require_repo_paths and not _is_repo_path(snapshot_path, repo_root):
            errors.append(f"line {line_no}: assessment_snapshot_json must be absolute repo path under {repo_root}")
        if require_existing_files and not _path_exists(snapshot_path):
            errors.append(f"line {line_no}: assessment_snapshot_json path not found")

    success_row_count = entry.get("success_row_count")
    if success_row_count is not None and (not isinstance(success_row_count, int) or success_row_count < 0):
        errors.append(f"line {line_no}: success_row_count must be null or non-negative integer")

    http_code_counts = entry.get("http_code_counts")
    if http_code_counts is not None:
        if not isinstance(http_code_counts, dict):
            errors.append(f"line {line_no}: http_code_counts must be null or object")
        else:
            for code, count in http_code_counts.items():
                if not isinstance(code, str) or not code.isdigit():
                    errors.append(f"line {line_no}: http_code_counts key must be digit string")
                if not isinstance(count, int) or count < 0:
                    errors.append(f"line {line_no}: http_code_counts value must be non-negative integer")

    note_class_counts = entry.get("note_class_counts")
    if note_class_counts is not None:
        if not isinstance(note_class_counts, dict):
            errors.append(f"line {line_no}: note_class_counts must be null or object")
        else:
            for note_key, count in note_class_counts.items():
                if not isinstance(note_key, str) or not note_key.strip():
                    errors.append(f"line {line_no}: note_class_counts key must be non-empty string")
                if not isinstance(count, int) or count < 0:
                    errors.append(f"line {line_no}: note_class_counts value must be non-negative integer")

    return errors


def validate_history(
    history_path: Path,
    repo_root: Path,
    require_repo_paths: bool,
    require_snapshot_for_assess: bool = False,
    require_existing_files: bool = False,
) -> List[str]:
    errors: List[str] = []
    if not history_path.exists():
        return [f"history file not found: {history_path}"]

    for idx, line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            errors.append(f"line {idx}: empty line is not allowed")
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {idx}: invalid JSON")
            continue
        if not isinstance(parsed, dict):
            errors.append(f"line {idx}: entry must be object")
            continue
        errors.extend(
            validate_entry(
                parsed,
                idx,
                repo_root,
                require_repo_paths=require_repo_paths,
                require_snapshot_for_assess=require_snapshot_for_assess,
                require_existing_files=require_existing_files,
            )
        )
    return errors


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_jsonl)
    repo_root = Path(args.repo_root)
    errors = validate_history(
        history_path,
        repo_root,
        require_repo_paths=args.require_repo_paths,
        require_snapshot_for_assess=args.require_snapshot_for_assess,
        require_existing_files=args.require_existing_files,
    )
    if errors:
        for item in errors:
            print(item, file=sys.stderr)
        return 2
    print(f"history validation passed: {history_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
