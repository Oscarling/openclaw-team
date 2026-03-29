from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_delivery_signal as signal


class ProjectDeliverySignalTests(unittest.TestCase):
    def test_build_signal_with_blocking_signal(self) -> None:
        payload = {
            "delivery_state": "blocked_external_provider",
            "blocking_signal": {
                "stage": "handshake_gate",
                "reason": "provider_account_arrearage",
            },
            "blocking_action": "暂停 replay 重试，先恢复 provider account 账务状态（Arrearage/overdue-payment）后再重跑 onboarding gate。",
            "onboarding_latest": {
                "block_reason": "provider_account_arrearage",
                "timestamp": "2026-03-29T14:48:40",
            },
        }
        extracted = signal.build_signal(payload)
        self.assertEqual(extracted["delivery_state"], "blocked_external_provider")
        self.assertEqual(extracted["blocking_stage"], "handshake_gate")
        self.assertEqual(extracted["blocking_reason"], "provider_account_arrearage")
        self.assertIn("暂停 replay 重试", extracted["blocking_action"])
        self.assertEqual(extracted["onboarding_block_reason"], "provider_account_arrearage")
        self.assertEqual(extracted["onboarding_timestamp"], "2026-03-29T14:48:40")

    def test_build_signal_handles_missing_optional_fields(self) -> None:
        extracted = signal.build_signal({"delivery_state": "ready_for_replay"})
        self.assertEqual(extracted["delivery_state"], "ready_for_replay")
        self.assertEqual(extracted["blocking_stage"], "")
        self.assertEqual(extracted["blocking_reason"], "")
        self.assertEqual(extracted["blocking_action"], "")
        self.assertEqual(extracted["onboarding_block_reason"], "")
        self.assertEqual(extracted["onboarding_timestamp"], "")

    def test_render_tsv_with_header(self) -> None:
        rendered = signal._render_tsv(
            {
                "delivery_state": "blocked_external_provider",
                "blocking_stage": "handshake_gate",
                "blocking_reason": "provider_account_arrearage",
                "blocking_action": "pause",
                "onboarding_block_reason": "provider_account_arrearage",
                "onboarding_timestamp": "2026-03-29T14:48:40",
            },
            with_header=True,
        )
        lines = rendered.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("delivery_state", lines[0])
        self.assertIn("blocked_external_provider", lines[1])

    def test_main_require_delivery_state_fails_when_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-") as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            argv = [
                "project_delivery_signal.py",
                "--status-json",
                str(path),
                "--require-delivery-state",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = signal.main()
            self.assertEqual(code, 2)

    def test_load_payload_rejects_non_object(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-") as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(json.dumps(["not-object"]), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                signal._load_payload(path)

    def test_main_require_blocking_context_fails_when_blocked_without_signal(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-") as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(
                json.dumps(
                    {
                        "delivery_state": "blocked_external_provider",
                        "onboarding_latest": {"block_reason": "provider_account_arrearage"},
                    }
                ),
                encoding="utf-8",
            )
            argv = [
                "project_delivery_signal.py",
                "--status-json",
                str(path),
                "--require-delivery-state",
                "--require-blocking-context",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = signal.main()
            self.assertEqual(code, 2)

    def test_main_require_blocking_context_passes_for_ready(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-") as tmp:
            path = Path(tmp) / "status.json"
            path.write_text(
                json.dumps(
                    {
                        "delivery_state": "ready_for_replay",
                        "onboarding_latest": {},
                    }
                ),
                encoding="utf-8",
            )
            argv = [
                "project_delivery_signal.py",
                "--status-json",
                str(path),
                "--require-delivery-state",
                "--require-blocking-context",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = signal.main()
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
