from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import project_delivery_status as status


def _backlog_markdown(
    *,
    chain_status: dict[str, str],
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
            self.assertEqual(payload["backlog"]["status_counts"]["done"], 9)

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
            md = status._to_markdown(payload)
            self.assertIn("no latest onboarding summary found", md)


if __name__ == "__main__":
    unittest.main()
