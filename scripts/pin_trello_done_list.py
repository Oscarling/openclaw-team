#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


DONE_LIST_NAME_CANDIDATES = ("done", "完成", "completed", "complete")
EXPORT_PATTERN = re.compile(r"^(?P<prefix>\s*export\s+)(?P<name>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>.*?)(?P<suffix>\s*)$")
VAR_REFERENCE_PATTERN = re.compile(r"^\$(?:\{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)\}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Resolve the Trello Done list id for a board and pin it into a shell env file "
            "such as /tmp/trello_env.sh."
        )
    )
    parser.add_argument(
        "--env-file",
        default="/tmp/trello_env.sh",
        help="Shell env file containing Trello credentials and board id.",
    )
    parser.add_argument("--board-id", default=None, help="Explicit Trello board id override.")
    parser.add_argument("--done-list-id", default=None, help="Explicit Done list id override. Skips API lookup.")
    parser.add_argument("--done-list-name", default=None, help="Preferred Done list name when resolving by board.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the resolved TRELLO_DONE_LIST_ID into the env file and archive the prior file first.",
    )
    return parser.parse_args()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _strip_shell_quotes(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def parse_exports(env_file: Path) -> tuple[list[str], dict[str, str]]:
    text = env_file.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    exports: dict[str, str] = {}
    for line in lines:
        match = EXPORT_PATTERN.match(line.rstrip("\n"))
        if not match:
            continue
        exports[match.group("name")] = _strip_shell_quotes(match.group("value"))
    return lines, exports


def _resolve_export_reference(name: str, exports: dict[str, str], seen: set[str] | None = None) -> str | None:
    if seen is None:
        seen = set()
    if name in seen:
        return None
    seen.add(name)
    raw = exports.get(name)
    if raw is None:
        return None
    match = VAR_REFERENCE_PATTERN.match(raw)
    if not match:
        return raw
    target = match.group("braced") or match.group("plain")
    if not target:
        return raw
    return _resolve_export_reference(target, exports, seen)


def _pick_env_from_exports(exports: dict[str, str], primary: str, alias: str) -> tuple[str | None, str]:
    primary_val = _resolve_export_reference(primary, exports)
    if primary_val:
        return primary_val, primary
    alias_val = _resolve_export_reference(alias, exports)
    if alias_val:
        return alias_val, alias
    return None, "missing"


def _normalize_list_name(name: str) -> str:
    return "".join(str(name or "").strip().lower().split())


def _shell_single_quote(value: str) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def _fetch_board_lists(
    *,
    board_id: str,
    api_key: str,
    api_token: str,
    urlopen: Callable[..., Any],
) -> list[dict[str, Any]]:
    query = urllib.parse.urlencode(
        {
            "key": api_key,
            "token": api_token,
            "fields": "id,name,closed,pos",
        }
    )
    url = f"https://api.trello.com/1/boards/{board_id}/lists?{query}"
    request = urllib.request.Request(url, method="GET")
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Unable to resolve Trello Done list: HTTP {exc.code}; response_preview={body[:300]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Unable to resolve Trello Done list before HTTP response: {exc.__class__.__name__}: {exc.reason}"
        ) from exc

    payload = json.loads(body)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Trello list response shape")
    normalized: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def resolve_done_list(
    *,
    exports: dict[str, str],
    board_id_override: str | None,
    done_list_id_override: str | None,
    done_list_name_override: str | None,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    board_id = (board_id_override or _resolve_export_reference("TRELLO_BOARD_ID", exports) or "").strip()
    if done_list_id_override:
        return {
            "done_list_id": done_list_id_override.strip(),
            "done_list_name": done_list_name_override,
            "board_id": board_id or None,
            "resolution": "explicit_done_list_id",
            "credential_source": "not_needed",
        }

    api_key, key_source = _pick_env_from_exports(exports, "TRELLO_API_KEY", "TRELLO_KEY")
    api_token, token_source = _pick_env_from_exports(exports, "TRELLO_API_TOKEN", "TRELLO_TOKEN")
    if not api_key or not api_token:
        raise RuntimeError("Missing Trello credentials in env file: expected TRELLO_API_KEY/TRELLO_API_TOKEN or aliases")
    if not board_id:
        raise RuntimeError("Missing TRELLO_BOARD_ID in env file and no --board-id override was supplied")

    lists = _fetch_board_lists(
        board_id=board_id,
        api_key=api_key,
        api_token=api_token,
        urlopen=urlopen,
    )
    target_names: list[str] = []
    if done_list_name_override:
        target_names.append(_normalize_list_name(done_list_name_override))
    target_names.extend(_normalize_list_name(name) for name in DONE_LIST_NAME_CANDIDATES)
    deduped_targets = [name for i, name in enumerate(target_names) if name and name not in target_names[:i]]

    for candidate in lists:
        if candidate.get("closed"):
            continue
        current_name = _normalize_list_name(str(candidate.get("name") or ""))
        if current_name in deduped_targets:
            done_list_id = str(candidate.get("id") or "").strip()
            if not done_list_id:
                raise RuntimeError("Resolved Trello Done list id is empty")
            return {
                "done_list_id": done_list_id,
                "done_list_name": candidate.get("name"),
                "board_id": board_id,
                "resolution": "board_list_lookup",
                "credential_source": f"{key_source}+{token_source}",
            }

    raise RuntimeError("Unable to resolve Trello Done list from board lists")


def render_updated_env(lines: list[str], *, done_list_id: str) -> str:
    rendered = list(lines)
    export_line = f"export TRELLO_DONE_LIST_ID={_shell_single_quote(done_list_id)}\n"
    for index, line in enumerate(rendered):
        match = EXPORT_PATTERN.match(line.rstrip("\n"))
        if match and match.group("name") == "TRELLO_DONE_LIST_ID":
            rendered[index] = export_line
            break
    else:
        if rendered and not rendered[-1].endswith("\n"):
            rendered[-1] = rendered[-1] + "\n"
        rendered.append(export_line)
    return "".join(rendered)


def pin_done_list_id(
    env_file: Path,
    *,
    board_id_override: str | None,
    done_list_id_override: str | None,
    done_list_name_override: str | None,
    apply: bool,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    if not env_file.exists():
        raise RuntimeError(f"Env file does not exist: {env_file}")

    lines, exports = parse_exports(env_file)
    resolved = resolve_done_list(
        exports=exports,
        board_id_override=board_id_override,
        done_list_id_override=done_list_id_override,
        done_list_name_override=done_list_name_override,
        urlopen=urlopen,
    )
    updated_text = render_updated_env(lines, done_list_id=resolved["done_list_id"])

    result = {
        "status": "resolved" if not apply else "updated",
        "env_file": str(env_file),
        "board_id": resolved.get("board_id"),
        "done_list_id": resolved["done_list_id"],
        "done_list_name": resolved.get("done_list_name"),
        "resolution": resolved["resolution"],
        "credential_source": resolved["credential_source"],
        "applied": apply,
    }

    if not apply:
        return result

    backup_path = env_file.with_name(f"{env_file.name}.bak-{utc_stamp()}")
    shutil.copy2(env_file, backup_path)
    env_file.write_text(updated_text, encoding="utf-8")
    result["backup_file"] = str(backup_path)
    return result


def main() -> int:
    args = parse_args()
    result = pin_done_list_id(
        Path(args.env_file).expanduser().resolve(),
        board_id_override=args.board_id,
        done_list_id_override=args.done_list_id,
        done_list_name_override=args.done_list_name,
        apply=args.apply,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
