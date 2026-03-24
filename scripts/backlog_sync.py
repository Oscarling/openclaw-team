#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import backlog_lint


ISSUE_NUMBER_PATTERN = re.compile(r"^#\d+$")
ISSUE_URL_PATTERN = re.compile(r"^https://github\.com/[^/]+/[^/]+/issues/\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check GitHub issue mirroring for PROJECT_BACKLOG.md.")
    parser.add_argument("--path", default="PROJECT_BACKLOG.md", help="Backlog file path.")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print the actionable mirror report without failing missing issue links.",
    )
    return parser.parse_args()


def issue_reference_kind(value: str) -> str:
    stripped = value.strip()
    if stripped == "-":
        return "missing"
    if stripped.startswith("deferred:"):
        return "deferred"
    if ISSUE_NUMBER_PATTERN.match(stripped):
        return "issue_number"
    if ISSUE_URL_PATTERN.match(stripped):
        return "issue_url"
    return "invalid"


def mirror_required(item: dict[str, str]) -> bool:
    item_type = item.get("type", "")
    status = item.get("status", "")
    phase = item.get("phase", "")
    return (
        item_type != "future"
        and phase == "now"
        and status in {"planned", "active", "blocked"}
    )


def collect_sync_issues(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    parse_items, parse_errors = backlog_lint.parse_backlog(path)
    if parse_errors:
        return parse_errors, []

    lint_errors = backlog_lint.validate_items(parse_items)
    if lint_errors:
        return lint_errors, []

    errors: list[str] = []
    required_items: list[dict[str, str]] = []

    for item in parse_items:
        if not mirror_required(item):
            continue
        required_items.append(item)
        issue_kind = issue_reference_kind(item.get("issue", "-"))
        if issue_kind == "missing":
            errors.append(f"{item['id']}: phase=now actionable item is missing a mirrored GitHub issue")
        elif issue_kind == "deferred":
            errors.append(f"{item['id']}: phase=now actionable item cannot use deferred issue mirroring")
        elif issue_kind == "invalid":
            errors.append(f"{item['id']}: issue field is not a valid GitHub issue reference")

    return errors, required_items


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    errors, required_items = collect_sync_issues(path)

    print("Backlog issue mirror report:")
    if required_items:
        for item in required_items:
            print(f"- {item['id']}: {item['title']} -> {item.get('issue', '-')}")
    else:
        print("- No phase=now actionable items require issue mirroring.")

    if errors and not args.report_only:
        print("Backlog issue mirror check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    if errors and args.report_only:
        print("Backlog issue mirror report contains unresolved items, but report-only mode is enabled.")
        return 0

    print(f"Backlog issue mirror check passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
