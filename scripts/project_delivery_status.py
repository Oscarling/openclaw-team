#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


CRITICAL_PROVIDER_CHAIN_IDS = [
    "BL-20260326-099",
]
DEFAULT_ONBOARDING_SUMMARY_JSON = "runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json"
REPLAY_CANARY_CLOSEOUT_ID = "BL-20260329-160"
FINALIZATION_CLOSEOUT_ID = "BL-20260329-162"
BLOCKING_ACTIONS_BY_REASON = {
    "provider_account_arrearage": (
        "暂停 replay 重试，先恢复 provider account 账务状态（Arrearage/overdue-payment）后再重跑 onboarding gate。"
    ),
    "invalid_api_key": "更换有效 provider key 后再重跑 onboarding gate。",
    "leaked_api_key": "替换已泄露 key，并确认新 key 未触发风控封禁后再重跑 onboarding gate。",
    "forbidden_or_gateway_policy": "切换可用 provider/base 或联系平台解除访问策略限制后再重跑 onboarding gate。",
    "auth_or_access_policy_block": "修复鉴权/访问策略阻塞（key/base 权限）后再重跑 onboarding gate。",
    "transport_or_dns_failure": "先修复网络/DNS 连通性，再重跑 onboarding gate。",
    "chain_not_clear": "优先清理 BL-092~BL-099 阻塞链，再推进握手与 replay。",
    "promotion_pending_after_handshake": "握手已通过，继续执行 controlled replay 验证并记录晋级证据。",
    "controlled_replay_blocked_after_handshake": "握手已通过，先定位并修复 controlled replay 阶段阻塞后再晋级。",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def _repo_scoped_path(path: Path, repo_root: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def _parse_backlog(backlog_path: Path) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw in backlog_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("### BL-"):
            if current:
                items.append(current)
            current = {"id": line.replace("### ", "", 1).strip()}
            continue
        if not current or not line.startswith("- "):
            continue
        if ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        key = key.strip()
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


def _derive_post_handshake_block_reason(item: dict[str, str] | None) -> str:
    if not item:
        return ""
    source_text = " ".join(
        [
            str(item.get("source", "")),
            str(item.get("done_when", "")),
            str(item.get("evidence", "")),
        ]
    ).lower()
    if (
        "provider_account_arrearage" in source_text
        or "arrearage" in source_text
        or "overdue-payment" in source_text
        or "overdue payment" in source_text
    ):
        return "provider_account_arrearage"
    if "controlled replay" in source_text and "block" in source_text:
        return "controlled_replay_blocked_after_handshake"
    return ""


def _build_delivery_state(
    *,
    chain_summary: dict[str, Any],
    onboarding_latest: dict[str, Any] | None,
    chain_index: dict[str, dict[str, str]],
) -> tuple[str, list[str], dict[str, str]]:
    next_steps: list[str] = []
    blocking_signal: dict[str, str] = {}
    onboarding_status = ""
    onboarding_block_reason = ""
    if onboarding_latest:
        onboarding_status = str(onboarding_latest.get("status", "")).strip().lower()
        onboarding_block_reason = str(onboarding_latest.get("block_reason", "")).strip()

    if not chain_summary["is_clear"]:
        bl099 = chain_index.get("BL-20260326-099")
        ids_text = "~".join(chain_summary["ids"]) if len(chain_summary["ids"]) > 1 else chain_summary["ids"][0]
        next_steps.append(f"先清理 provider/base 阻塞链（{ids_text}）。")
        replay_block_reason = _derive_post_handshake_block_reason(bl099)
        if onboarding_status == "ready" and bl099 and bl099.get("status", "") != "done":
            if replay_block_reason == "provider_account_arrearage":
                next_steps.append("当前阻塞已从握手转移到 controlled replay：provider 账务状态 `Arrearage`。")
                blocking_signal = {
                    "stage": "controlled_replay_promotion",
                    "reason": "provider_account_arrearage",
                }
            elif replay_block_reason:
                next_steps.append("当前阻塞已从握手转移到 controlled replay（握手已 ready，但晋级被外部条件拦截）。")
                blocking_signal = {
                    "stage": "controlled_replay_promotion",
                    "reason": replay_block_reason,
                }
            else:
                next_steps.append("当前阻塞已从握手转移到 controlled replay（握手已 ready，但晋级尚未完成）。")
                blocking_signal = {
                    "stage": "controlled_replay_promotion",
                    "reason": "promotion_pending_after_handshake",
                }
        elif onboarding_block_reason and onboarding_block_reason.lower() != "none":
            next_steps.append(f"当前握手阻塞原因：{onboarding_block_reason}。")
            blocking_signal = {
                "stage": "handshake_gate",
                "reason": onboarding_block_reason,
            }
        else:
            blocking_signal = {
                "stage": "provider_chain",
                "reason": "chain_not_clear",
            }
        next_steps.append(
            "当拿到新的 provider/base+key 后运行：python3 scripts/provider_onboarding_gate.py --stamp <YYYYMMDD> --require-ready"
        )
        return "blocked_external_provider", next_steps, blocking_signal

    if onboarding_status == "ready":
        canary_closeout = chain_index.get(REPLAY_CANARY_CLOSEOUT_ID)
        finalization_closeout = chain_index.get(FINALIZATION_CLOSEOUT_ID)
        if finalization_closeout and finalization_closeout.get("status", "") == "done":
            next_steps.append(
                "formal finalization 已完成（git push + Trello Done 已闭环）；当前主线进入稳定维护阶段。"
            )
        elif canary_closeout and canary_closeout.get("status", "") == "done":
            next_steps.append(
                "controlled replay 与 canary 已完成，进入 finalization preflight（配置 GIT_PUSH_REMOTE/GIT_PUSH_BRANCH/TRELLO_* 并清理工作区）。"
            )
        else:
            next_steps.append("进入 controlled replay 与 canary 收尾流程。")
        return "ready_for_replay", next_steps, blocking_signal

    if onboarding_status == "blocked":
        next_steps.append("链路条目虽清空，但握手仍 blocked；先恢复可用 provider/base 路由。")
        next_steps.append(
            "恢复后执行：python3 scripts/provider_onboarding_gate.py --stamp <YYYYMMDD> --require-ready"
        )
        blocking_signal = {
            "stage": "handshake_gate",
            "reason": onboarding_block_reason or "blocked_unknown",
        }
        return "blocked_external_provider", next_steps, blocking_signal

    next_steps.append("缺少可判定的 onboarding 最新状态，先执行 provider_onboarding_gate 刷新摘要。")
    blocking_signal = {
        "stage": "unknown",
        "reason": "missing_onboarding_signal",
    }
    return "unknown_waiting_signal", next_steps, blocking_signal


def _derive_blocking_action(delivery_state: str, blocking_signal: dict[str, str]) -> str:
    if delivery_state == "ready_for_replay":
        return ""
    reason = str(blocking_signal.get("reason", "")).strip()
    if not reason:
        return ""
    return BLOCKING_ACTIONS_BY_REASON.get(reason, "")


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
    summary_json_path_display = summary_json_path
    summary_json_path_fs = _repo_scoped_path(summary_json_path, repo_root)
    default_summary_path_display = Path(DEFAULT_ONBOARDING_SUMMARY_JSON)
    default_summary_path_fs = _repo_scoped_path(default_summary_path_display, repo_root)
    if (
        not summary_json_path_fs.exists()
        and summary_json_path_display != default_summary_path_display
        and default_summary_path_fs.exists()
    ):
        summary_json_path_display = default_summary_path_display
        summary_json_path_fs = default_summary_path_fs
    if summary_json_path_fs.exists():
        onboarding_summary = _load_json(summary_json_path_fs)
        latest = onboarding_summary.get("latest")
        if isinstance(latest, dict):
            onboarding_latest = latest

    chain_index = {item["id"]: item for item in backlog_items}
    chain_summary = _build_chain_summary(backlog_items)
    delivery_state, next_steps, blocking_signal = _build_delivery_state(
        chain_summary=chain_summary,
        onboarding_latest=onboarding_latest,
        chain_index=chain_index,
    )
    blocking_action = _derive_blocking_action(delivery_state, blocking_signal)

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
        "onboarding_summary_path": str(summary_json_path_display),
        "blocking_signal": blocking_signal,
        "blocking_action": blocking_action,
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
    signal = payload.get("blocking_signal", {})
    if isinstance(signal, dict) and signal:
        lines.append(f"- blocking_stage: `{signal.get('stage', '')}`")
        lines.append(f"- blocking_reason: `{signal.get('reason', '')}`")
    blocking_action = str(payload.get("blocking_action", "")).strip()
    if blocking_action:
        lines.append(f"- blocking_action: `{blocking_action}`")
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
        default=DEFAULT_ONBOARDING_SUMMARY_JSON,
        help="Path to provider onboarding summary json.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root used for branch detection.")
    parser.add_argument("--current-branch", default="", help="Optional current branch override.")
    parser.add_argument("--output-json", default="", help="Optional output json path.")
    parser.add_argument("--output-md", default="", help="Optional markdown report path.")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit with code 2 unless delivery_state is ready_for_replay.",
    )
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
    if args.require_ready and payload.get("delivery_state") != "ready_for_replay":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
