from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import project_delivery_status as status


def _backlog_markdown(
    *,
    chain_status: dict[str, str],
    chain_source: dict[str, str] | None = None,
) -> str:
    lines = []
    lines.extend(
        [
            "## Backlog Dashboard",
            "",
            "### BL-20260324-001",
            "- title: Bootstrap governance",
            "- status: done",
            "- phase: now",
            "- priority: p0",
            "- depends_on: -",
            "",
            "### BL-20260324-009",
            "- title: Revisit reviewer-count enforcement if a second human maintainer joins",
            "- status: planned",
            "- phase: later",
            "- priority: p3",
            "- depends_on: -",
            "",
        ]
    )
    for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS:
        lines.extend(
            [
                f"### {item_id}",
                f"- title: {item_id} title",
                f"- status: {chain_status[item_id]}",
                "- phase: next",
                "- priority: p1",
                "- depends_on: -",
                f"- source: {(chain_source or {}).get(item_id, '-')}",
                "",
            ]
        )
    return "\n".join(lines)


class ProjectDeliveryStatusTests(unittest.TestCase):
    def test_build_status_payload_reports_external_blockers(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            chain_status["BL-20260326-099"] = "blocked"
            backlog_path.write_text(_backlog_markdown(chain_status=chain_status), encoding="utf-8")
            summary_path.write_text(
                json.dumps(
                    {
                        "latest": {
                            "status": "blocked",
                            "block_reason": "auth_or_access_policy_block",
                            "timestamp": "2026-03-28T12:26:50",
                        }
                    }
                ),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="feat/provider-onboarding-resilience-hardening",
            )

            self.assertEqual(payload["delivery_state"], "blocked_external_provider")
            chain = payload["critical_provider_chain"]
            self.assertFalse(chain["is_clear"])
            self.assertEqual(chain["blockers"], ["BL-20260326-099"])
            self.assertIn("provider/base", " ".join(payload["next_steps"]))
            self.assertEqual(payload["blocking_signal"]["stage"], "handshake_gate")
            self.assertEqual(payload["blocking_signal"]["reason"], "auth_or_access_policy_block")
            self.assertIn("修复鉴权", payload["blocking_action"])

    def test_build_status_payload_ready_for_replay_when_chain_clear_and_ready(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            backlog_path.write_text(_backlog_markdown(chain_status=chain_status), encoding="utf-8")
            summary_path.write_text(
                json.dumps({"latest": {"status": "ready", "block_reason": "", "timestamp": "2026-03-28T16:00:00"}}),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="main",
            )

            self.assertEqual(payload["delivery_state"], "ready_for_replay")
            self.assertTrue(payload["critical_provider_chain"]["is_clear"])
            self.assertEqual(payload["backlog"]["status_counts"]["done"], 1 + len(status.CRITICAL_PROVIDER_CHAIN_IDS))
            self.assertEqual(payload["blocking_signal"], {})
            self.assertEqual(payload["blocking_action"], "")
            self.assertIn("controlled replay 与 canary", " ".join(payload["next_steps"]))

    def test_build_status_payload_points_to_preflight_after_canary_closeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            backlog_text = _backlog_markdown(chain_status=chain_status)
            backlog_text += (
                "\n### BL-20260329-160\n"
                "- title: DeepSeek canary closeout\n"
                "- status: done\n"
                "- phase: next\n"
                "- priority: p1\n"
                "- depends_on: BL-20260329-159\n"
            )
            backlog_path.write_text(backlog_text, encoding="utf-8")
            summary_path.write_text(
                json.dumps({"latest": {"status": "ready", "block_reason": "", "timestamp": "2026-03-29T16:50:47"}}),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="feat/provider-onboarding-resilience-hardening",
            )

            self.assertEqual(payload["delivery_state"], "ready_for_replay")
            joined = " ".join(payload["next_steps"])
            self.assertIn("finalization preflight", joined)
            self.assertNotIn("进入 controlled replay 与 canary 收尾流程。", joined)

    def test_build_status_payload_points_to_stable_stage_after_finalization_closeout(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            backlog_text = _backlog_markdown(chain_status=chain_status)
            backlog_text += (
                "\n### BL-20260329-160\n"
                "- title: DeepSeek canary closeout\n"
                "- status: done\n"
                "- phase: next\n"
                "- priority: p1\n"
                "- depends_on: BL-20260329-159\n"
                "\n### BL-20260329-162\n"
                "- title: Formal finalization completion\n"
                "- status: done\n"
                "- phase: next\n"
                "- priority: p1\n"
                "- depends_on: BL-20260329-161\n"
            )
            backlog_path.write_text(backlog_text, encoding="utf-8")
            summary_path.write_text(
                json.dumps({"latest": {"status": "ready", "block_reason": "", "timestamp": "2026-03-29T17:20:00"}}),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="main",
            )

            self.assertEqual(payload["delivery_state"], "ready_for_replay")
            joined = " ".join(payload["next_steps"])
            self.assertIn("formal finalization 已完成", joined)
            self.assertNotIn("finalization preflight", joined)

    def test_build_status_payload_mentions_arrearage_when_handshake_ready_but_bl099_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            chain_status["BL-20260326-099"] = "blocked"
            chain_source = {
                "BL-20260326-099": "controlled replay attempts later hit provider-side Arrearage (http_400) and block promotion"
            }
            backlog_path.write_text(
                _backlog_markdown(chain_status=chain_status, chain_source=chain_source),
                encoding="utf-8",
            )
            summary_path.write_text(
                json.dumps({"latest": {"status": "ready", "block_reason": "none", "timestamp": "2026-03-29T14:16:38"}}),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="feat/provider-onboarding-resilience-hardening",
            )

            self.assertEqual(payload["delivery_state"], "blocked_external_provider")
            joined = " ".join(payload["next_steps"])
            self.assertIn("Arrearage", joined)
            self.assertNotIn("当前握手阻塞原因：none", joined)
            self.assertEqual(payload["blocking_signal"]["stage"], "controlled_replay_promotion")
            self.assertEqual(payload["blocking_signal"]["reason"], "provider_account_arrearage")
            self.assertIn("暂停 replay 重试", payload["blocking_action"])

    def test_build_status_payload_detects_overdue_payment_alias_for_post_handshake_block(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            chain_status["BL-20260326-099"] = "blocked"
            chain_source = {
                "BL-20260326-099": "controlled replay remained blocked due to provider overdue-payment response"
            }
            backlog_path.write_text(
                _backlog_markdown(chain_status=chain_status, chain_source=chain_source),
                encoding="utf-8",
            )
            summary_path.write_text(
                json.dumps({"latest": {"status": "ready", "block_reason": "none", "timestamp": "2026-03-29T14:16:38"}}),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="feat/provider-onboarding-resilience-hardening",
            )

            self.assertEqual(payload["delivery_state"], "blocked_external_provider")
            self.assertEqual(payload["blocking_signal"]["stage"], "controlled_replay_promotion")
            self.assertEqual(payload["blocking_signal"]["reason"], "provider_account_arrearage")
            self.assertIn("恢复 provider account 账务状态", payload["blocking_action"])

    def test_build_status_payload_reports_unknown_when_summary_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            summary_path = root / "missing-summary.json"

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            backlog_path.write_text(_backlog_markdown(chain_status=chain_status), encoding="utf-8")

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=summary_path,
                repo_root=root,
                current_branch="feat/x",
            )

            self.assertEqual(payload["delivery_state"], "unknown_waiting_signal")
            self.assertEqual(payload["onboarding_latest"], {})
            self.assertEqual(payload["blocking_signal"]["stage"], "unknown")
            self.assertEqual(payload["blocking_signal"]["reason"], "missing_onboarding_signal")
            self.assertEqual(payload["blocking_action"], "")
            md = status._to_markdown(payload)
            self.assertIn("no latest onboarding summary found", md)
            self.assertIn("blocking_stage", md)

    def test_build_status_payload_falls_back_to_default_summary_when_requested_path_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-status-") as tmp:
            root = Path(tmp)
            backlog_path = root / "PROJECT_BACKLOG.md"
            requested_missing_path = Path("runtime_archives/bl100/provider_onboarding_summary.json")
            default_summary_path = root / status.DEFAULT_ONBOARDING_SUMMARY_JSON
            default_summary_path.parent.mkdir(parents=True, exist_ok=True)

            chain_status = {item_id: "done" for item_id in status.CRITICAL_PROVIDER_CHAIN_IDS}
            backlog_path.write_text(_backlog_markdown(chain_status=chain_status), encoding="utf-8")
            default_summary_path.write_text(
                json.dumps(
                    {
                        "latest": {
                            "status": "ready",
                            "block_reason": "none",
                            "timestamp": "2026-03-29T16:05:39",
                        }
                    }
                ),
                encoding="utf-8",
            )

            payload = status.build_status_payload(
                backlog_path=backlog_path,
                summary_json_path=requested_missing_path,
                repo_root=root,
                current_branch="main",
            )

            self.assertEqual(payload["delivery_state"], "ready_for_replay")
            self.assertEqual(payload["onboarding_summary_path"], status.DEFAULT_ONBOARDING_SUMMARY_JSON)
            self.assertEqual(payload["onboarding_latest"]["status"], "ready")

    def test_main_require_ready_returns_2_when_not_ready(self) -> None:
        args = SimpleNamespace(
            backlog="PROJECT_BACKLOG.md",
            summary_json="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
            repo_root=".",
            current_branch="",
            output_json="",
            output_md="",
            require_ready=True,
        )
        with (
            mock.patch.object(status, "parse_args", return_value=args),
            mock.patch.object(
                status,
                "build_status_payload",
                return_value={
                    "delivery_state": "blocked_external_provider",
                    "backlog": {"done": 1, "total": 2, "completion_percent": 50},
                    "critical_provider_chain": {"items": []},
                    "onboarding_latest": {},
                    "next_steps": [],
                },
            ),
            mock.patch("builtins.print"),
        ):
            code = status.main()
        self.assertEqual(code, 2)

    def test_main_require_ready_returns_0_when_ready(self) -> None:
        args = SimpleNamespace(
            backlog="PROJECT_BACKLOG.md",
            summary_json="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
            repo_root=".",
            current_branch="",
            output_json="",
            output_md="",
            require_ready=True,
        )
        with (
            mock.patch.object(status, "parse_args", return_value=args),
            mock.patch.object(
                status,
                "build_status_payload",
                return_value={
                    "delivery_state": "ready_for_replay",
                    "backlog": {"done": 2, "total": 2, "completion_percent": 100},
                    "critical_provider_chain": {"items": []},
                    "onboarding_latest": {},
                    "next_steps": [],
                },
            ),
            mock.patch("builtins.print"),
        ):
            code = status.main()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
