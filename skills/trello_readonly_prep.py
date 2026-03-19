from __future__ import annotations

import argparse
import json
import os
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


def smoke_read_trello(list_id: str | None, board_id: str | None, limit: int) -> dict[str, Any]:
    api_key = os.environ.get("TRELLO_API_KEY")
    api_token = os.environ.get("TRELLO_API_TOKEN")
    if not api_key or not api_token:
        return {
            "status": "blocked",
            "reason": "Missing TRELLO_API_KEY or TRELLO_API_TOKEN",
            "missing": [k for k in ["TRELLO_API_KEY", "TRELLO_API_TOKEN"] if not os.environ.get(k)],
        }

    if not list_id and not board_id:
        return {
            "status": "blocked",
            "reason": "Missing read scope id: provide --list-id/--board-id or env TRELLO_LIST_ID/TRELLO_BOARD_ID",
        }

    params = {
        "key": api_key,
        "token": api_token,
        "fields": "id,idShort,name,desc,idList,idBoard,dateLastActivity,labels",
        "limit": max(1, int(limit)),
    }
    if list_id:
        url = f"https://api.trello.com/1/lists/{list_id}/cards"
    else:
        url = f"https://api.trello.com/1/boards/{board_id}/cards"

    resp = requests.get(url, params=params, timeout=20)
    if resp.status_code != 200:
        return {
            "status": "blocked",
            "reason": f"Read-only Trello request failed: HTTP {resp.status_code}",
            "response_preview": resp.text[:300],
        }

    data = resp.json()
    if not isinstance(data, list):
        return {
            "status": "blocked",
            "reason": "Unexpected Trello response shape (expected list)",
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
        "mapped_preview": mapped_preview,
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
