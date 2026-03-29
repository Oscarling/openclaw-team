#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SIGNAL_SCRIPT = SCRIPT_DIR / "project_delivery_signal.py"
CONSISTENCY_SCRIPT = SCRIPT_DIR / "project_delivery_signal_consistency_check.py"


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build delivery signal artifacts (json+tsv) and optionally verify consistency.")
    parser.add_argument("--status-json", required=True, help="Path to project_delivery_status JSON payload.")
    parser.add_argument(
        "--output-prefix",
        default="/tmp/project_delivery_status.signal",
        help="Output prefix for generated signal artifacts (.json/.tsv).",
    )
    parser.add_argument("--signal-json", default="", help="Optional explicit output path for signal JSON.")
    parser.add_argument("--signal-tsv", default="", help="Optional explicit output path for signal TSV.")
    parser.add_argument(
        "--output-summary-json",
        default="",
        help="Optional summary JSON path for bundle run metadata.",
    )
    parser.add_argument(
        "--with-header",
        action="store_true",
        help="Include TSV header row.",
    )
    parser.add_argument(
        "--require-delivery-state",
        action="store_true",
        help="Fail when delivery_state is missing/empty.",
    )
    parser.add_argument(
        "--require-blocking-context",
        action="store_true",
        help="Fail when non-ready delivery_state lacks blocking stage/reason.",
    )
    parser.add_argument(
        "--no-consistency-check",
        action="store_true",
        help="Skip status-vs-signal consistency verification.",
    )
    return parser.parse_args()


def _load_status_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("status payload must be a JSON object")
    return payload


def _validate_requirements(
    signal: dict[str, str],
    *,
    require_delivery_state: bool,
    require_blocking_context: bool,
) -> str:
    if require_delivery_state and not signal.get("delivery_state", "").strip():
        return "delivery_state missing in status payload"
    if require_blocking_context:
        delivery_state = str(signal.get("delivery_state", "")).strip()
        if delivery_state and delivery_state != "ready_for_replay":
            stage = str(signal.get("blocking_stage", "")).strip()
            reason = str(signal.get("blocking_reason", "")).strip()
            if not stage or not reason:
                return "blocking context missing: non-ready delivery_state requires blocking_stage and blocking_reason"
    return ""


def _resolve_output_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    prefix = Path(args.output_prefix)
    signal_json = Path(args.signal_json) if args.signal_json else Path(f"{prefix}.json")
    signal_tsv = Path(args.signal_tsv) if args.signal_tsv else Path(f"{prefix}.tsv")
    return signal_json, signal_tsv


def main() -> int:
    args = parse_args()
    status_path = Path(args.status_json)
    if not status_path.exists():
        print(f"status json not found: {status_path}", file=sys.stderr)
        return 2

    signal_module = _load_module(SIGNAL_SCRIPT, "project_delivery_signal")
    consistency_module = _load_module(CONSISTENCY_SCRIPT, "project_delivery_signal_consistency_check")

    status_payload = _load_status_payload(status_path)
    signal = signal_module.build_signal(status_payload)

    validation_error = _validate_requirements(
        signal,
        require_delivery_state=args.require_delivery_state,
        require_blocking_context=args.require_blocking_context,
    )
    if validation_error:
        print(validation_error, file=sys.stderr)
        return 2

    signal_json_path, signal_tsv_path = _resolve_output_paths(args)
    signal_json_path.parent.mkdir(parents=True, exist_ok=True)
    signal_tsv_path.parent.mkdir(parents=True, exist_ok=True)

    signal_json_path.write_text(json.dumps(signal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    signal_tsv_path.write_text(
        signal_module._render_tsv(signal, with_header=bool(args.with_header)),
        encoding="utf-8",
    )

    summary: dict[str, Any] = {
        "status_json": str(status_path),
        "signal_json": str(signal_json_path),
        "signal_tsv": str(signal_tsv_path),
        "delivery_state": signal.get("delivery_state", ""),
        "blocking_stage": signal.get("blocking_stage", ""),
        "blocking_reason": signal.get("blocking_reason", ""),
        "blocking_action": signal.get("blocking_action", ""),
        "consistency_check": "skipped" if args.no_consistency_check else "pending",
    }

    if not args.no_consistency_check:
        expected = signal_module.build_signal(status_payload)
        actual_json = consistency_module._load_json_object(signal_json_path)
        actual_tsv = consistency_module._parse_signal_tsv(signal_tsv_path)
        errors: list[str] = []
        errors.extend(consistency_module._diff_signal(expected, actual_json, "signal_json"))
        errors.extend(consistency_module._diff_signal(expected, actual_tsv, "signal_tsv"))
        if errors:
            for line in errors:
                print(line, file=sys.stderr)
            return 2
        summary["consistency_check"] = "passed"

    if args.output_summary_json:
        summary_path = Path(args.output_summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
