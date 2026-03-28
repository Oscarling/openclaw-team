#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


CRITICAL_PROVIDER_CHAIN_IDS = [
    "BL-20260326-092",
    "BL-20260326-093",
    "BL-20260326-094",
    "BL-20260326-095",
    "BL-20260326-096",
    "BL-20260326-097",
    "BL-20260326-098",
    "BL-20260326-099",
]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _parse_backlog(backlog_path: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in backlog_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("### BL-"):
            if current:
                items.append(current)
            current = {
                "id": line.replace("### ", "", 1).strip(),
                "title": "",
                "status": "",
                "phase": "",
                "priority": "",
                "depends_on": "",
            }
            continue
        if not current or not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        key = key.strip()
        if key in current:
            current[key] = value.strip()
    if current:
        items.append(current)
    return items


def _detect_current_branch(repo_root: Path) -> str:
    try:
        output = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            text=True,
        ).strip()
    except Exception:
        return "unknown"
    return output or "unknown"


def _build_chain_summary(backlog_items: list[dict[str, str]]) -> dict[str, Any]:
    index = {item["id"]: item for item in backlog_items}
    chain_items: list[dict[str, str]] = []
    blockers: list[str] = []
    for item_id in CRITICAL_PROVIDER_CHAIN_IDS:
        item = index.get(item_id)
        if not item:
            chain_items.append(
                {
                    "id": item_id,
                    "status": "missing",
                    "phase": "",
                    "priority": "",
                    "title": "missing_from_backlog",
                }
            )
            blockers.append(item_id)
            continue
        chain_items.append(
            {
                "id": item_id,
                "status": item.get("status", ""),
                "phase": item.get("phase", ""),
                "priority": item.get("priority", ""),
                "title": item.get("title", ""),
            }
        )
        if item.get("status", "") != "done":
            blockers.append(item_id)
    return {
        "ids": CRITICAL_PROVIDER_CHAIN_IDS,
        "items": chain_items,
        "is_clear": len(blockers) == 0,
        "blockers": blockers,
    }


def _build_delivery_state(
    *,
    chain_summary: dict[str, Any],
    onboarding_latest: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    next_steps: list[str] = []
    onboarding_status = ""
    onboarding_block_reason = ""
    if onboarding_latest:
        onboarding_status = str(onboarding_latest.get("status", "")).strip().lower()
        onboarding_block_reason = str(onboarding_latest.get("block_reason", "")).strip()

    if not chain_summary["is_clear"]:
        next_steps.append("先清理 provider/base 阻塞链（BL-092~BL-099）。")
        if onboarding_block_reason:
            next_steps.append(f"当前握手阻塞原因：{onboarding_block_reason}。")
        next_steps.append(
            "当拿到新的 provider/base+key 后运行：python3 scripts/provider_onboarding_gate.py --stamp <YYYYMMDD> --require-ready"
        )
        return "blocked_external_provider", next_steps

    if onboarding_status == "ready":
        next_steps.append("进入 controlled replay 与 canary 收尾流程。")
        return "ready_for_replay", next_steps

    if onboarding_status == "blocked":
        next_steps.append("链路条目虽清空，但握手仍 blocked；先恢复可用 provider/base 路由。")
        next_steps.append(
            "恢复后执行：python3 scripts/provider_onboarding_gate.py --stamp <YYYYMMDD> --require-ready"
        )
        return "blocked_external_provider", next_steps

    next_steps.append("缺少可判定的 onboarding 最新状态，先执行 provider_onboarding_gate 刷新摘要。")
    return "unknown_waiting_signal", next_steps


def build_status_payload(
    *,
    backlog_path: Path,
    summary_json_path: Path,
    repo_root: Path,
    current_branch: str | None,
) -> dict[str, Any]:
    backlog_items = _parse_backlog(backlog_path)
    status_counts = Counter(item.get("status", "") for item in backlog_items)
    phase_counts = Counter(item.get("phase", "") for item in backlog_items)
    total = len(backlog_items)
    done_count = status_counts.get("done", 0)
    completion_percent = round((done_count / total) * 100, 2) if total else 0.0

    onboarding_summary: dict[str, Any] | None = None
    onboarding_latest: dict[str, Any] | None = None
    if summary_json_path.exists():
        onboarding_summary = _load_json(summary_json_path)
        latest = onboarding_summary.get("latest")
        if isinstance(latest, dict):
            onboarding_latest = latest

    chain_summary = _build_chain_summary(backlog_items)
    delivery_state, next_steps = _build_delivery_state(
        chain_summary=chain_summary,
        onboarding_latest=onboarding_latest,
    )

    return {
        "status": "ok",
        "delivery_state": delivery_state,
        "repo_root": str(repo_root),
        "current_branch": current_branch or _detect_current_branch(repo_root),
        "backlog": {
            "path": str(backlog_path),
            "total": total,
            "done": done_count,
            "completion_percent": completion_percent,
            "status_counts": dict(status_counts),
            "phase_counts": dict(phase_counts),
        },
        "critical_provider_chain": chain_summary,
        "onboarding_latest": onboarding_latest or {},
        "onboarding_summary_path": str(summary_json_path),
        "next_steps": next_steps,
    }


def _to_markdown(payload: dict[str, Any]) -> str:
    backlog = payload["backlog"]
    chain = payload["critical_provider_chain"]
    lines = [
        "# Project Delivery Status",
        "",
        f"- delivery_state: `{payload['delivery_state']}`",
        f"- current_branch: `{payload['current_branch']}`",
        f"- completion: `{backlog['done']}/{backlog['total']}` ({backlog['completion_percent']}%)",
        "",
        "## Critical Provider Chain",
    ]
    for item in chain["items"]:
        lines.append(
            f"- `{item['id']}` status=`{item['status']}` phase=`{item['phase']}` priority=`{item['priority']}` title={item['title']}"
        )
    lines.append("")
    lines.append("## Onboarding Latest")
    if payload["onboarding_latest"]:
        latest = payload["onboarding_latest"]
        lines.append(f"- status: `{latest.get('status', '')}`")
        lines.append(f"- block_reason: `{latest.get('block_reason', '')}`")
        lines.append(f"- timestamp: `{latest.get('timestamp', '')}`")
    else:
        lines.append("- no latest onboarding summary found")
    lines.append("")
    lines.append("## Next Steps")
    for step in payload["next_steps"]:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a non-technical project delivery status payload.")
    parser.add_argument("--backlog", default="PROJECT_BACKLOG.md", help="Path to backlog markdown file.")
    parser.add_argument(
        "--summary-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Path to provider onboarding summary json.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root used for branch detection.")
    parser.add_argument("--current-branch", default="", help="Optional current branch override.")
    parser.add_argument("--output-json", default="", help="Optional output json path.")
    parser.add_argument("--output-md", default="", help="Optional markdown report path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_status_payload(
        backlog_path=Path(args.backlog),
        summary_json_path=Path(args.summary_json),
        repo_root=Path(args.repo_root).resolve(),
        current_branch=args.current_branch or None,
    )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output_json:
        Path(args.output_json).write_text(rendered + "\n", encoding="utf-8")
    if args.output_md:
        Path(args.output_md).write_text(_to_markdown(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
