#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


ITEM_HEADING = "### "
ITEMS_SECTION = "## Backlog Items"
ID_PATTERN = re.compile(r"^BL-\d{8}-\d{3}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ISSUE_PATTERN = re.compile(r"^(?:-|#\d+|https?://\S+|deferred:.+)$")
FIELD_PATTERN = re.compile(r"^- ([a-z_]+):\s*(.*)$")

REQUIRED_FIELDS = [
    "title",
    "type",
    "status",
    "phase",
    "priority",
    "owner",
    "depends_on",
    "start_when",
    "done_when",
    "source",
    "link",
    "issue",
    "evidence",
    "last_reviewed_at",
    "opened_at",
]

ALLOWED_TYPES = {"mainline", "sideline", "blocker", "debt", "future"}
ALLOWED_STATUS = {"planned", "active", "parked", "blocked", "done"}
ALLOWED_PHASES = {"now", "next", "later"}
ALLOWED_PRIORITIES = {"p0", "p1", "p2", "p3"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate PROJECT_BACKLOG.md structure and policy.")
    parser.add_argument("--path", default="PROJECT_BACKLOG.md", help="Backlog file path.")
    return parser.parse_args()


def _parse_date(label: str, value: str, errors: list[str], item_id: str) -> date | None:
    if not DATE_PATTERN.match(value):
        errors.append(f"{item_id}: {label} must use YYYY-MM-DD, got {value!r}")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"{item_id}: {label} is not a real calendar date: {value!r}")
        return None


def _split_depends(value: str) -> list[str]:
    if value == "-":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_backlog(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    if not path.exists():
        return [], [f"{path} does not exist"]

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_items = False
    current_id: str | None = None
    current_item: dict[str, str] = {}
    items: list[dict[str, str]] = []

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if stripped == ITEMS_SECTION:
            in_items = True
            continue
        if not in_items:
            continue
        if stripped.startswith("## ") and stripped != ITEMS_SECTION:
            break
        if not stripped:
            continue
        if stripped.startswith(ITEM_HEADING):
            if current_id is not None:
                items.append({"id": current_id, **current_item})
            current_id = stripped[len(ITEM_HEADING) :].strip()
            current_item = {}
            continue
        if current_id is None:
            errors.append(f"{path}:{lineno}: unexpected content before first backlog item heading: {stripped!r}")
            continue
        match = FIELD_PATTERN.match(stripped)
        if not match:
            errors.append(f"{path}:{lineno}: expected '- key: value' entry under {current_id}, got {stripped!r}")
            continue
        key, value = match.groups()
        current_item[key] = value.strip() or "-"

    if current_id is not None:
        items.append({"id": current_id, **current_item})

    if not in_items:
        errors.append(f"{path}: missing '{ITEMS_SECTION}' section")
    if in_items and not items:
        errors.append(f"{path}: backlog items section is empty")
    return items, errors


def validate_items(items: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    all_ids = [item.get("id", "") for item in items]

    for item in items:
        item_id = item.get("id", "").strip()
        if not ID_PATTERN.match(item_id):
            errors.append(f"{item_id or '<missing-id>'}: backlog id must match BL-YYYYMMDD-NNN")
        if item_id in seen_ids:
            errors.append(f"{item_id}: duplicate backlog id")
        seen_ids.add(item_id)

        missing = [field for field in REQUIRED_FIELDS if field not in item]
        for field in missing:
            errors.append(f"{item_id}: missing required field {field}")

        extra = sorted(set(item) - set(REQUIRED_FIELDS) - {"id"})
        for field in extra:
            errors.append(f"{item_id}: unknown field {field}")

        for field in REQUIRED_FIELDS:
            value = item.get(field, "").strip()
            if not value:
                errors.append(f"{item_id}: field {field} must not be empty")

        item_type = item.get("type", "")
        if item_type and item_type not in ALLOWED_TYPES:
            errors.append(f"{item_id}: type must be one of {sorted(ALLOWED_TYPES)}, got {item_type!r}")

        status = item.get("status", "")
        if status and status not in ALLOWED_STATUS:
            errors.append(f"{item_id}: status must be one of {sorted(ALLOWED_STATUS)}, got {status!r}")

        phase = item.get("phase", "")
        if phase and phase not in ALLOWED_PHASES:
            errors.append(f"{item_id}: phase must be one of {sorted(ALLOWED_PHASES)}, got {phase!r}")

        priority = item.get("priority", "")
        if priority and priority not in ALLOWED_PRIORITIES:
            errors.append(f"{item_id}: priority must be one of {sorted(ALLOWED_PRIORITIES)}, got {priority!r}")

        owner = item.get("owner", "")
        if phase == "now" and owner == "-":
            errors.append(f"{item_id}: phase=now items must declare an owner")

        if item_type == "future" and phase != "later":
            errors.append(f"{item_id}: type=future items must use phase=later")

        issue = item.get("issue", "")
        if issue and not ISSUE_PATTERN.match(issue):
            errors.append(f"{item_id}: issue must be '-', '#123', URL, or 'deferred:reason', got {issue!r}")

        opened = _parse_date("opened_at", item.get("opened_at", ""), errors, item_id)
        reviewed = _parse_date("last_reviewed_at", item.get("last_reviewed_at", ""), errors, item_id)
        if opened and reviewed and reviewed < opened:
            errors.append(f"{item_id}: last_reviewed_at cannot be earlier than opened_at")

        deps = _split_depends(item.get("depends_on", "-"))
        for dep in deps:
            if not ID_PATTERN.match(dep):
                errors.append(f"{item_id}: depends_on contains invalid id {dep!r}")
            elif dep not in all_ids:
                errors.append(f"{item_id}: depends_on references unknown backlog id {dep}")

        if status == "done" and item.get("evidence", "-") == "-":
            errors.append(f"{item_id}: done items must replace evidence '-' with a concrete proof link")

    return errors


def lint_backlog(path: Path) -> list[str]:
    items, parse_errors = parse_backlog(path)
    if parse_errors:
        return parse_errors
    return validate_items(items)


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    errors = lint_backlog(path)
    if errors:
        print("Backlog lint failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Backlog lint passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
