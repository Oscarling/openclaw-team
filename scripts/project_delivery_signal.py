#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract concise delivery signal from project delivery status JSON.")
    parser.add_argument("--status-json", required=True, help="Path to project_delivery_status JSON payload.")
    parser.add_argument(
        "--output-format",
        choices=("tsv", "json"),
        default="tsv",
        help="Output format (default: tsv).",
    )
    parser.add_argument(
        "--with-header",
        action="store_true",
        help="Include header row for TSV output.",
    )
    parser.add_argument(
        "--require-delivery-state",
        action="store_true",
        help="Exit non-zero when delivery_state is empty.",
    )
    parser.add_argument(
        "--require-blocking-context",
        action="store_true",
        help="Exit non-zero when non-ready delivery_state lacks blocking stage/reason.",
    )
    return parser.parse_args()


def _load_payload(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("status payload must be a JSON object")
    return data


def build_signal(payload: dict[str, Any]) -> dict[str, str]:
    delivery_state = str(payload.get("delivery_state", "")).strip()
    blocking_signal = payload.get("blocking_signal")
    if not isinstance(blocking_signal, dict):
        blocking_signal = {}
    onboarding_latest = payload.get("onboarding_latest")
    if not isinstance(onboarding_latest, dict):
        onboarding_latest = {}
    return {
        "delivery_state": delivery_state,
        "blocking_stage": str(blocking_signal.get("stage", "")).strip(),
        "blocking_reason": str(blocking_signal.get("reason", "")).strip(),
        "blocking_action": str(payload.get("blocking_action", "")).strip(),
        "onboarding_block_reason": str(onboarding_latest.get("block_reason", "")).strip(),
        "onboarding_timestamp": str(onboarding_latest.get("timestamp", "")).strip(),
    }


def _render_tsv(signal: dict[str, str], with_header: bool) -> str:
    columns = [
        "delivery_state",
        "blocking_stage",
        "blocking_reason",
        "blocking_action",
        "onboarding_block_reason",
        "onboarding_timestamp",
    ]
    lines: list[str] = []
    if with_header:
        lines.append("\t".join(columns))
    lines.append("\t".join(signal.get(column, "") for column in columns))
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    payload = _load_payload(Path(args.status_json))
    signal = build_signal(payload)
    if args.require_delivery_state and not signal["delivery_state"]:
        print("delivery_state missing in status payload", file=sys.stderr)
        return 2
    if args.require_blocking_context:
        delivery_state = signal["delivery_state"]
        if delivery_state and delivery_state != "ready_for_replay":
            if not signal["blocking_stage"] or not signal["blocking_reason"]:
                print(
                    "blocking context missing: non-ready delivery_state requires blocking_stage and blocking_reason",
                    file=sys.stderr,
                )
                return 2
    if args.output_format == "json":
        print(json.dumps(signal, ensure_ascii=False, indent=2))
    else:
        print(_render_tsv(signal, with_header=args.with_header), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
