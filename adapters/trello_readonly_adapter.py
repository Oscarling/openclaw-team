from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

CONTRACT_TITLE_SUFFIX = "(best-effort reviewable attempt)"
CONTRACT_NOTE = (
    "Execution contract: treat this as a best-effort, evidence-backed PDF extraction/conversion attempt. "
    "Do not claim OCR success without evidence. If full OCR/Excel conversion is not honestly achievable, "
    "return reviewable intermediate artifacts, explicit limitations, and next-step guidance. "
    "Keep behavior deterministic and limited to declared local artifacts."
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _label_slug(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"\s+", "_", text)
    text = re.sub(r"[^a-z0-9_.:-]", "", text)
    text = text.strip("_.:-")
    if not text:
        text = "label"
    return text[:32]


def _normalize_labels(raw_labels: Any) -> list[str]:
    labels: list[str] = []
    if not isinstance(raw_labels, list):
        return labels
    for item in raw_labels:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("color") or "").strip()
        else:
            name = str(item).strip()
        if not name:
            continue
        labels.append(_label_slug(name))
    deduped: list[str] = []
    seen = set()
    for label in labels:
        if label in seen:
            continue
        seen.add(label)
        deduped.append(label)
    return deduped


def _augment_title(raw_title: str) -> str:
    title = raw_title.strip()
    lowered = title.lower()
    if any(token in lowered for token in ("best-effort", "best effort", "reviewable", "evidence-backed")):
        return title
    return f"{title} {CONTRACT_TITLE_SUFFIX}"


def _augment_description(raw_description: str, card_id: str) -> str:
    description = raw_description.strip()
    if not description:
        description = f"[trello] card {card_id} has no description; using title as fallback context."
    if CONTRACT_NOTE.lower() in description.lower():
        return description
    return f"{description}\n\n{CONTRACT_NOTE}"


def required_readonly_env() -> dict[str, list[str]]:
    return {
        "credentials": ["TRELLO_API_KEY", "TRELLO_API_TOKEN"],
        "credentials_aliases": ["TRELLO_KEY", "TRELLO_TOKEN"],
        "credentials_priority": ["TRELLO_API_KEY/TRELLO_API_TOKEN", "TRELLO_KEY/TRELLO_TOKEN"],
        "scope": ["TRELLO_BOARD_ID", "TRELLO_LIST_ID"],
        "scope_rule": ["TRELLO_BOARD_ID or TRELLO_LIST_ID (either one)"],
    }


def map_trello_card_to_external_input(
    card: dict[str, Any],
    *,
    board_id: str | None = None,
    list_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(card, dict):
        raise RuntimeError("Trello card payload must be an object")

    card_id = str(card.get("id") or "").strip()
    if not card_id:
        raise RuntimeError("Trello card id is required")

    title = str(card.get("name") or "").strip()
    if not title:
        raise RuntimeError("Trello card name is required")
    title = _augment_title(title)

    description = _augment_description(str(card.get("desc") or ""), card_id)

    mapped_labels = _normalize_labels(card.get("labels"))
    mapped_labels.extend(["trello", "readonly", "best_effort", "evidence_backed", "reviewable"])
    mapped_labels = sorted(set(mapped_labels))

    normalized = {
        "origin_id": f"trello:{card_id}",
        "title": title,
        "description": description,
        "labels": mapped_labels,
        "metadata": {
            "source_system": "trello",
            "card_id": card_id,
            "card_short_id": card.get("idShort"),
            "board_id": board_id or card.get("idBoard"),
            "list_id": list_id or card.get("idList"),
            "date_last_activity": card.get("dateLastActivity"),
            "readonly_mapped_at": _utc_now(),
            "contract_profile": "best_effort_evidence_backed",
            "ocr_claim_policy": "do_not_claim_success_without_evidence",
            "fallback_policy": "return_reviewable_artifacts_limitations_and_next_steps_when_full_conversion_is_not_honestly_achievable",
        },
        "source": {
            "provider": "trello",
            "mode": "readonly",
            "card_id": card_id,
            "board_id": board_id or card.get("idBoard"),
            "list_id": list_id or card.get("idList"),
        },
        "request_type": "pdf_to_excel_ocr",
        "input": {
            "input_dir": "~/Desktop/pdf样本",
            "output_xlsx": "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx",
            "ocr": "auto",
            "dry_run": False,
        },
    }
    return normalized
