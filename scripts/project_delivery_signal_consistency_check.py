#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


SIGNAL_COLUMNS = [
    "delivery_state",
    "blocking_stage",
    "blocking_reason",
    "blocking_action",
    "onboarding_block_reason",
    "onboarding_timestamp",
]
SIGNAL_MODULE_PATH = Path(__file__).resolve().parent / "project_delivery_signal.py"


def _load_signal_module():
    spec = importlib.util.spec_from_file_location("project_delivery_signal", SIGNAL_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load signal module from {SIGNAL_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate consistency between delivery status JSON and extracted signal artifacts.")
    parser.add_argument("--status-json", required=True, help="Path to project_delivery_status JSON payload.")
    parser.add_argument("--signal-json", default="", help="Optional signal JSON path produced by project_delivery_signal.py.")
    parser.add_argument("--signal-tsv", default="", help="Optional signal TSV path produced by project_delivery_signal.py.")
    return parser.parse_args()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _parse_signal_tsv(path: Path) -> dict[str, str]:
    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"{path} is empty")
    if len(lines) > 2:
        raise RuntimeError(f"{path} must contain one signal row (optional header + single row)")
    if len(lines) == 1:
        row = lines[0]
    else:
        header = lines[0].split("\t")
        if header != SIGNAL_COLUMNS:
            raise RuntimeError(f"{path} header mismatch")
        row = lines[1]
    parts = row.split("\t")
    if len(parts) != len(SIGNAL_COLUMNS):
        raise RuntimeError(f"{path} row must have {len(SIGNAL_COLUMNS)} columns")
    return {key: value.strip() for key, value in zip(SIGNAL_COLUMNS, parts)}


def _diff_signal(expected: dict[str, str], actual: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    for key in SIGNAL_COLUMNS:
        exp = str(expected.get(key, "")).strip()
        got = str(actual.get(key, "")).strip()
        if exp != got:
            errors.append(f"{label}: {key} mismatch (expected={exp!r}, actual={got!r})")
    return errors


def main() -> int:
    args = parse_args()
    status_path = Path(args.status_json)
    if not status_path.exists():
        raise FileNotFoundError(f"status json not found: {status_path}")

    if not args.signal_json and not args.signal_tsv:
        raise RuntimeError("at least one of --signal-json or --signal-tsv is required")

    status_payload = _load_json_object(status_path)
    signal_module = _load_signal_module()
    expected = signal_module.build_signal(status_payload)

    errors: list[str] = []
    checked_targets: list[str] = []

    if args.signal_json:
        signal_json_path = Path(args.signal_json)
        if not signal_json_path.exists():
            raise FileNotFoundError(f"signal json not found: {signal_json_path}")
        actual_json = _load_json_object(signal_json_path)
        errors.extend(_diff_signal(expected, actual_json, "signal_json"))
        checked_targets.append(str(signal_json_path))

    if args.signal_tsv:
        signal_tsv_path = Path(args.signal_tsv)
        if not signal_tsv_path.exists():
            raise FileNotFoundError(f"signal tsv not found: {signal_tsv_path}")
        actual_tsv = _parse_signal_tsv(signal_tsv_path)
        errors.extend(_diff_signal(expected, actual_tsv, "signal_tsv"))
        checked_targets.append(str(signal_tsv_path))

    if errors:
        for line in errors:
            print(line)
        return 2

    print("delivery signal consistency passed:", ", ".join(checked_targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
