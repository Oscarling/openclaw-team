from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.trello_readonly_adapter import map_trello_card_to_external_input
from adapters.local_inbox_adapter import StandardizedInboxTask, normalize_local_inbox_payload
from argus_contracts import validate_task


INBOX_DIR = REPO_ROOT / "inbox"
PROCESSING_DIR = REPO_ROOT / "processing"
PROCESSED_DIR = REPO_ROOT / "processed"
REJECTED_DIR = REPO_ROOT / "rejected"
PREVIEW_DIR = REPO_ROOT / "preview"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


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


def _trello_auth_env() -> dict[str, Any]:
    api_key, key_source = _pick_env("TRELLO_API_KEY", "TRELLO_KEY")
    api_token, token_source = _pick_env("TRELLO_API_TOKEN", "TRELLO_TOKEN")
    return {
        "api_key": api_key,
        "api_token": api_token,
        "selected_names": {"key": key_source, "token": token_source},
        "priority": "TRELLO_API_* first, fallback to TRELLO_*",
        "presence": _presence_map(
            [
                "TRELLO_API_KEY",
                "TRELLO_KEY",
                "TRELLO_API_TOKEN",
                "TRELLO_TOKEN",
                "TRELLO_BOARD_ID",
                "TRELLO_LIST_ID",
            ]
        ),
    }


def _write_trello_payload_to_inbox(payload: dict[str, Any], card_id: str) -> Path:
    safe_card = re.sub(r"[^a-zA-Z0-9_.-]", "-", card_id).strip("-").lower() or "unknown-card"
    candidate = INBOX_DIR / f"trello-readonly-{safe_card}.json"
    if candidate.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = INBOX_DIR / f"trello-readonly-{safe_card}-{stamp}.json"
    candidate.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return candidate


def ingest_trello_readonly_once(
    *,
    board_id_override: str | None,
    list_id_override: str | None,
    limit: int,
) -> dict[str, Any]:
    auth = _trello_auth_env()
    api_key = auth["api_key"]
    api_token = auth["api_token"]

    if not api_key or not api_token:
        raise RuntimeError(
            "Missing Trello credentials: provide TRELLO_API_KEY/TRELLO_API_TOKEN or TRELLO_KEY/TRELLO_TOKEN"
        )

    board_id = (board_id_override or os.environ.get("TRELLO_BOARD_ID") or "").strip()
    list_id = (list_id_override or os.environ.get("TRELLO_LIST_ID") or "").strip()
    if not board_id and not list_id:
        raise RuntimeError(
            "Missing Trello scope id: set --trello-board-id/--trello-list-id or env TRELLO_BOARD_ID/TRELLO_LIST_ID"
        )

    scope_kind = "list" if list_id else "board"
    if list_id:
        url = f"https://api.trello.com/1/lists/{list_id}/cards"
    else:
        url = f"https://api.trello.com/1/boards/{board_id}/cards"
    params = {
        "key": api_key,
        "token": api_token,
        "fields": "id,idShort,name,desc,idList,idBoard,dateLastActivity,labels",
        "limit": max(1, int(limit)),
    }

    try:
        response = requests.get(url, params=params, timeout=20)
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Trello read-only request failed before HTTP response: {exc.__class__.__name__}"
        ) from exc

    if response.status_code != 200:
        body_preview = (response.text or "")[:300]
        raise RuntimeError(
            f"Trello read-only request failed: HTTP {response.status_code}; response_preview={body_preview}"
        )

    cards = response.json()
    if not isinstance(cards, list):
        raise RuntimeError("Unexpected Trello response shape (expected list)")

    written_files: list[str] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        mapped = map_trello_card_to_external_input(
            card,
            board_id=board_id or None,
            list_id=list_id or None,
        )
        card_id = str(card.get("id") or mapped.get("origin_id") or "unknown-card")
        path = _write_trello_payload_to_inbox(mapped, card_id)
        written_files.append(str(path))

    return {
        "status": "done",
        "scope_kind": scope_kind,
        "read_count": len(cards),
        "inbox_written": len(written_files),
        "inbox_files": written_files,
        "scope_presence": {
            "TRELLO_BOARD_ID": "set" if bool(board_id) else "missing",
            "TRELLO_LIST_ID": "set" if bool(list_id) else "missing",
        },
        "auth_env": {
            "selected_names": auth["selected_names"],
            "priority": auth["priority"],
            "presence": auth["presence"],
        },
    }


def move_with_suffix(src: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    candidate = target_dir / src.name
    if not candidate.exists():
        shutil.move(str(src), str(candidate))
        return candidate
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    candidate = target_dir / f"{src.stem}.{stamp}{src.suffix}"
    shutil.move(str(src), str(candidate))
    return candidate


def write_result_sidecar(target_file: Path, payload: dict[str, Any]) -> Path:
    sidecar = target_file.with_suffix(target_file.suffix + ".result.json")
    sidecar.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return sidecar


def load_seen_dedupe_keys() -> set[str]:
    seen: set[str] = set()
    for preview_file in PREVIEW_DIR.glob("*.json"):
        try:
            data = json.loads(preview_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        keys = data.get("dedupe_keys")
        if isinstance(keys, list):
            for key in keys:
                if isinstance(key, str) and key.strip():
                    seen.add(key.strip())

    for folder in (PROCESSED_DIR, REJECTED_DIR):
        for sidecar in folder.glob("*.result.json"):
            try:
                data = json.loads(sidecar.read_text(encoding="utf-8"))
            except Exception:
                continue
            keys = data.get("dedupe_keys")
            if isinstance(keys, list):
                for key in keys:
                    if isinstance(key, str) and key.strip():
                        seen.add(key.strip())
    return seen


def preview_id_for(standardized: StandardizedInboxTask) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", standardized.origin_id.lower()).strip("-")
    if not slug:
        slug = "inbox"
    slug = slug[:48]
    return f"preview-{slug}-{standardized.payload_hash[:12]}"


def build_preview_payload(
    *,
    standardized: StandardizedInboxTask,
    raw_payload: dict[str, Any],
    inbox_filename: str,
    preview_id: str,
) -> dict[str, Any]:
    request_type = str(raw_payload.get("request_type", "pdf_to_excel_ocr")).strip().lower()
    inputs = raw_payload.get("input", {})
    if not isinstance(inputs, dict):
        inputs = {}

    expected_artifacts: list[str] = []
    for task in (standardized.automation_task, standardized.critic_task):
        for artifact in task.get("expected_outputs", []):
            if isinstance(artifact, dict):
                path = artifact.get("path")
                if isinstance(path, str) and path.startswith("artifacts/"):
                    expected_artifacts.append(path)

    warnings: list[str] = []
    if str(inputs.get("ocr", "auto")).strip().lower() == "on":
        warnings.append("OCR forced on; ensure tesseract/pdftoppm dependencies are available.")
    output_xlsx = str(inputs.get("output_xlsx", "")).strip()
    if output_xlsx and not output_xlsx.startswith("artifacts/"):
        warnings.append("Requested output_xlsx is outside artifacts/; downstream worker may reject it.")
    if bool(inputs.get("dry_run", False)):
        warnings.append("This request asks for dry-run mode.")

    return {
        "preview_id": preview_id,
        "created_at": utc_now(),
        "approved": False,
        "source": {
            "kind": standardized.source.get("kind"),
            "origin_id": standardized.origin_id,
            "received_at": standardized.source.get("received_at") or utc_now(),
            "inbox_file": inbox_filename,
        },
        "external_input": {
            "title": standardized.title,
            "description": standardized.description,
            "labels": standardized.labels,
            "metadata": standardized.metadata,
            "request_type": request_type,
            "input": inputs,
        },
        "task_summary": {
            "automation": {
                "task_id": standardized.automation_task.get("task_id"),
                "worker": "automation",
                "task_type": standardized.automation_task.get("task_type"),
                "objective": standardized.automation_task.get("objective"),
                "expected_outputs": standardized.automation_task.get("expected_outputs"),
            },
            "critic": {
                "task_id": standardized.critic_task.get("task_id"),
                "worker": "critic",
                "task_type": standardized.critic_task.get("task_type"),
                "objective": standardized.critic_task.get("objective"),
                "expected_outputs": standardized.critic_task.get("expected_outputs"),
            },
        },
        "internal_tasks": {
            "automation": standardized.automation_task,
            "critic": standardized.critic_task,
        },
        "expected_artifacts": sorted(set(expected_artifacts)),
        "dedupe_keys": standardized.dedupe_keys,
        "risk_warnings": warnings,
        "execution": {
            "status": "pending_approval",
            "executed": False,
            "attempts": 0,
        },
    }


def process_one(processing_file: Path, seen_dedupe_keys: set[str]) -> dict[str, Any]:
    standardized = None
    preview_payload = None
    preview_path: Path | None = None

    try:
        with open(processing_file, encoding="utf-8") as f:
            raw_payload = json.load(f)

        standardized = normalize_local_inbox_payload(
            raw_payload,
            inbox_filename=processing_file.name,
            base_dir=REPO_ROOT,
        )

        duplicate_keys = [key for key in standardized.dedupe_keys if key in seen_dedupe_keys]
        if duplicate_keys:
            raise RuntimeError(
                "duplicate inbox input detected; keys="
                + ",".join(duplicate_keys)
            )

        auto_errors = validate_task(standardized.automation_task)
        critic_errors = validate_task(standardized.critic_task)
        if auto_errors or critic_errors:
            raise RuntimeError(
                "task_validate_failed "
                + json.dumps(
                    {"automation_errors": auto_errors, "critic_errors": critic_errors},
                    ensure_ascii=False,
                )
            )

        preview_id = preview_id_for(standardized)
        preview_path = PREVIEW_DIR / f"{preview_id}.json"
        if preview_path.exists():
            raise RuntimeError(f"duplicate preview_id detected: {preview_id}")

        preview_payload = build_preview_payload(
            standardized=standardized,
            raw_payload=raw_payload,
            inbox_filename=processing_file.name,
            preview_id=preview_id,
        )
        preview_path.write_text(
            json.dumps(preview_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        moved = move_with_suffix(processing_file, PROCESSED_DIR)

        if standardized:
            for key in standardized.dedupe_keys:
                seen_dedupe_keys.add(key)

        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": "processed",
                "decision": "preview_created_pending_approval",
                "decision_reason": "preview_created; waiting_for_explicit_approval",
                "origin_id": None if standardized is None else standardized.origin_id,
                "payload_hash": None if standardized is None else standardized.payload_hash,
                "dedupe_keys": [] if standardized is None else standardized.dedupe_keys,
                "title": None if standardized is None else standardized.title,
                "labels": [] if standardized is None else standardized.labels,
                "preview_id": preview_payload["preview_id"],
                "preview_file": str(preview_path),
            },
        )
        return {
            "status": "processed",
            "decision": "preview_created_pending_approval",
            "decision_reason": "preview_created; waiting_for_explicit_approval",
            "file": str(moved),
            "result_sidecar": str(sidecar),
            "preview_id": preview_payload["preview_id"],
            "preview_file": str(preview_path),
        }
    except Exception as exc:
        moved = move_with_suffix(processing_file, REJECTED_DIR)
        decision = "rejected"
        reason_text = str(exc)
        if "duplicate inbox input detected" in reason_text:
            decision = "duplicate_skipped"
        sidecar = write_result_sidecar(
            moved,
            {
                "ingested_at": utc_now(),
                "status": "rejected",
                "decision": decision,
                "decision_reason": reason_text,
                "error": reason_text,
                "origin_id": None if standardized is None else standardized.origin_id,
                "payload_hash": None if standardized is None else standardized.payload_hash,
                "dedupe_keys": [] if standardized is None else standardized.dedupe_keys,
                "title": None if standardized is None else standardized.title,
                "preview_file": None if preview_path is None else str(preview_path),
            },
        )
        if standardized:
            for key in standardized.dedupe_keys:
                seen_dedupe_keys.add(key)
        return {
            "status": "rejected",
            "decision": decision,
            "decision_reason": reason_text,
            "file": str(moved),
            "result_sidecar": str(sidecar),
            "error": reason_text,
        }


def claim_inbox_file(inbox_file: Path) -> Path:
    return move_with_suffix(inbox_file, PROCESSING_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest local inbox JSON and generate execution previews (approval required before dispatch)."
    )
    parser.add_argument("--once", action="store_true", help="Process current inbox files once and exit.")
    parser.add_argument(
        "--test-mode",
        choices=("off", "success", "partial", "failed", "transient_failed"),
        default="success",
        help="Reserved for compatibility. In preview mode ingest does not dispatch workers.",
    )
    parser.add_argument(
        "--trello-readonly-once",
        action="store_true",
        help=(
            "Fetch Trello cards in read-only mode, normalize via existing adapter, "
            "write to inbox, then continue standard preview-only ingest."
        ),
    )
    parser.add_argument(
        "--trello-board-id",
        default=None,
        help="Trello board id override for read-only ingestion.",
    )
    parser.add_argument(
        "--trello-list-id",
        default=None,
        help="Trello list id override for read-only ingestion.",
    )
    parser.add_argument(
        "--trello-limit",
        type=int,
        default=3,
        help="Max Trello cards to fetch for --trello-readonly-once.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()

    trello_readonly = None
    if args.trello_readonly_once:
        try:
            trello_readonly = ingest_trello_readonly_once(
                board_id_override=args.trello_board_id,
                list_id_override=args.trello_list_id,
                limit=args.trello_limit,
            )
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "status": "blocked",
                        "mode": "trello_readonly_once",
                        "reason": str(exc),
                        "auth_env": _trello_auth_env().get("presence"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1

    recovered_processing_files = sorted(PROCESSING_DIR.glob("*.json"))
    inbox_files = sorted(INBOX_DIR.glob("*.json"))
    if not recovered_processing_files and not inbox_files:
        payload: dict[str, Any] = {"status": "idle", "message": "No inbox files"}
        if trello_readonly is not None:
            payload["mode"] = "trello_readonly_once"
            payload["trello_readonly"] = trello_readonly
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    claimed_files: list[Path] = []
    for inbox_file in inbox_files:
        claimed_files.append(claim_inbox_file(inbox_file))

    processing_files = recovered_processing_files + claimed_files
    seen_dedupe_keys = load_seen_dedupe_keys()

    results = []
    for processing_file in processing_files:
        result = process_one(processing_file, seen_dedupe_keys)
        results.append(result)

    payload = {
        "status": "done",
        "processed": len([r for r in results if r["status"] == "processed"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "duplicate_skipped": len([r for r in results if r.get("decision") == "duplicate_skipped"]),
        "preview_created": len([r for r in results if r.get("decision") == "preview_created_pending_approval"]),
        "inbox_claimed": len(claimed_files),
        "processing_recovered": len(recovered_processing_files),
        "test_mode": args.test_mode,
        "results": results,
    }
    if trello_readonly is not None:
        payload["mode"] = "trello_readonly_once"
        payload["trello_readonly"] = trello_readonly
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ARGUS_BASE_DIR", str(REPO_ROOT))
    os.environ.setdefault("ARGUS_APP_HOST_PATH", str(REPO_ROOT))
    raise SystemExit(main())
