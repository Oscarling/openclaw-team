from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.trello_readonly_adapter import (  # noqa: E402
    map_trello_card_to_external_input,
    required_readonly_env,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Trello read-only preparation helper.")
    parser.add_argument(
        "--fixture",
        default=str(REPO_ROOT / "adapters" / "samples" / "trello_card_fixture.json"),
        help="Local Trello card fixture JSON path for offline mapping.",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "processing" / "trello_readonly_mapped_sample.json"),
        help="Where to write mapped local-inbox-compatible payload.",
    )
    parser.add_argument("--smoke-read", action="store_true", help="Run one read-only Trello API smoke check.")
    parser.add_argument("--board-id", default=None, help="Trello board id override for smoke check.")
    parser.add_argument("--list-id", default=None, help="Trello list id override for smoke check.")
    parser.add_argument("--limit", type=int, default=1, help="Read-only smoke card limit.")
    return parser.parse_args()


def load_fixture(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise RuntimeError("Fixture must be a JSON object")
    return payload


def write_mapped_payload(output_path: Path, payload: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _presence_map(names: list[str]) -> dict[str, str]:
    return {name: ("set" if os.environ.get(name) else "missing") for name in names}


def _pick_env(primary: str, alias: str) -> tuple[str | None, str]:
    primary_val = os.environ.get(primary)
    if primary_val:
        return primary_val, primary
    alias_val = os.environ.get(alias)
    if alias_val:
        return alias_val, alias
    return None, "missing"


def _classify_http_error(status_code: int, body_preview: str, scope_kind: str) -> tuple[str, str]:
    text = (body_preview or "").lower()
    if status_code == 401:
        if "invalid key" in text:
            return "invalid_key", "Read-only Trello auth failed: API key appears invalid (HTTP 401)."
        if "invalid token" in text or ("token" in text and "invalid" in text):
            return "invalid_token", "Read-only Trello auth failed: token appears invalid (HTTP 401)."
        if "unauthorized permission requested" in text or "scope" in text:
            return "token_scope_insufficient", "Read-only Trello auth failed: token scope appears insufficient (HTTP 401)."
        return "unauthorized_unknown", "Read-only Trello request unauthorized (HTTP 401)."

    if status_code == 403:
        if scope_kind == "board":
            return "token_no_board_access", "Read-only Trello request forbidden: token has no access to this board (HTTP 403)."
        if scope_kind == "list":
            return "token_no_list_access", "Read-only Trello request forbidden: token has no access to this list (HTTP 403)."
        return "forbidden", "Read-only Trello request forbidden (HTTP 403)."

    if status_code == 404:
        if scope_kind == "board":
            return "board_not_found_or_no_access", "Read-only Trello request failed: board not found (or not visible) (HTTP 404)."
        if scope_kind == "list":
            return "list_not_found_or_no_access", "Read-only Trello request failed: list not found (or not visible) (HTTP 404)."
        return "not_found", "Read-only Trello request failed: resource not found (HTTP 404)."

    return "http_error", f"Read-only Trello request failed: HTTP {status_code}."


def _redact_sensitive(text: str, api_key: str | None, api_token: str | None) -> str:
    out = text or ""
    if api_key:
        out = out.replace(api_key, "***redacted_key***")
    if api_token:
        out = out.replace(api_token, "***redacted_token***")
    out = re.sub(r"([?&]key=)[^&\\s]+", r"\1***redacted_key***", out)
    out = re.sub(r"([?&]token=)[^&\\s]+", r"\1***redacted_token***", out)
    return out


def smoke_read_trello(list_id: str | None, board_id: str | None, limit: int) -> dict[str, Any]:
    api_key, key_source = _pick_env("TRELLO_API_KEY", "TRELLO_KEY")
    api_token, token_source = _pick_env("TRELLO_API_TOKEN", "TRELLO_TOKEN")
    env_presence = _presence_map(
        [
            "TRELLO_API_KEY",
            "TRELLO_KEY",
            "TRELLO_API_TOKEN",
            "TRELLO_TOKEN",
            "TRELLO_BOARD_ID",
            "TRELLO_LIST_ID",
        ]
    )
    auth_env = {
        "selected_names": {"key": key_source, "token": token_source},
        "priority": "TRELLO_API_* first, fallback to TRELLO_*",
        "presence": env_presence,
    }
    if not api_key or not api_token:
        return {
            "status": "blocked",
            "reason": "Missing Trello credentials: provide TRELLO_API_KEY/TRELLO_API_TOKEN or TRELLO_KEY/TRELLO_TOKEN",
            "missing": [
                name
                for name in ["TRELLO_API_KEY|TRELLO_KEY", "TRELLO_API_TOKEN|TRELLO_TOKEN"]
                if (name.startswith("TRELLO_API_KEY") and not api_key)
                or (name.startswith("TRELLO_API_TOKEN") and not api_token)
            ],
            "auth_env": auth_env,
        }

    if not list_id and not board_id:
        return {
            "status": "blocked",
            "reason": "Missing read scope id: provide --list-id/--board-id or env TRELLO_LIST_ID/TRELLO_BOARD_ID",
            "auth_env": auth_env,
        }

    params = {
        "key": api_key,
        "token": api_token,
        "fields": "id,idShort,name,desc,idList,idBoard,dateLastActivity,labels",
        "limit": max(1, int(limit)),
    }
    scope_kind = "list" if list_id else "board"
    if list_id:
        url = f"https://api.trello.com/1/lists/{list_id}/cards"
    else:
        url = f"https://api.trello.com/1/boards/{board_id}/cards"

    try:
        resp = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        return {
            "status": "blocked",
            "reason": f"Read-only Trello request failed before HTTP response: {exc.__class__.__name__}",
            "error_type": "request_exception",
            "response_preview": _redact_sensitive(str(exc), api_key, api_token)[:300],
            "auth_env": auth_env,
        }

    if resp.status_code != 200:
        response_preview = _redact_sensitive(resp.text, api_key, api_token)[:300]
        error_code, detailed_reason = _classify_http_error(resp.status_code, response_preview, scope_kind)
        return {
            "status": "blocked",
            "reason": detailed_reason,
            "error_code": error_code,
            "http_status": resp.status_code,
            "response_preview": response_preview,
            "auth_env": auth_env,
        }

    data = resp.json()
    if not isinstance(data, list):
        return {
            "status": "blocked",
            "reason": "Unexpected Trello response shape (expected list)",
            "http_status": resp.status_code,
            "auth_env": auth_env,
        }

    mapped_preview = None
    if data:
        mapped_preview = map_trello_card_to_external_input(
            data[0],
            board_id=board_id,
            list_id=list_id,
        )

    return {
        "status": "pass",
        "read_count": len(data),
        "scope": {"board_id": board_id, "list_id": list_id},
        "scope_kind": scope_kind,
        "mapped_preview": mapped_preview,
        "auth_env": auth_env,
        "note": "Read-only GET only. No write operations performed.",
    }


def main() -> int:
    args = parse_args()

    fixture = load_fixture(Path(args.fixture).expanduser().resolve())
    mapped = map_trello_card_to_external_input(fixture)
    write_mapped_payload(Path(args.output).expanduser().resolve(), mapped)

    smoke_result = {
        "status": "skipped",
        "reason": "smoke check not requested",
    }
    if args.smoke_read:
        smoke_result = smoke_read_trello(
            list_id=args.list_id or os.environ.get("TRELLO_LIST_ID"),
            board_id=args.board_id or os.environ.get("TRELLO_BOARD_ID"),
            limit=args.limit,
        )

    payload = {
        "status": "done",
        "fixture": str(Path(args.fixture).expanduser().resolve()),
        "mapped_output": str(Path(args.output).expanduser().resolve()),
        "required_env": required_readonly_env(),
        "smoke_read": smoke_result,
        "mode": "trello_readonly_prep",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
