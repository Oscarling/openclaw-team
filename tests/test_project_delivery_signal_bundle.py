from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_delivery_signal_bundle as bundle


class ProjectDeliverySignalBundleTests(unittest.TestCase):
    def _write_status(self, root: Path, payload: dict) -> Path:
        path = root / "status.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_main_writes_json_tsv_and_summary_with_consistency(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-bundle-") as tmp:
            root = Path(tmp)
            status = self._write_status(
                root,
                {
                    "delivery_state": "blocked_external_provider",
                    "blocking_signal": {
                        "stage": "handshake_gate",
                        "reason": "provider_account_arrearage",
                    },
                    "onboarding_latest": {
                        "block_reason": "provider_account_arrearage",
                        "timestamp": "2026-03-29T14:48:40",
                    },
                },
            )
            prefix = root / "bundle_signal"
            summary = root / "bundle_summary.json"
            argv = [
                "project_delivery_signal_bundle.py",
                "--status-json",
                str(status),
                "--output-prefix",
                str(prefix),
                "--require-delivery-state",
                "--require-blocking-context",
                "--with-header",
                "--output-summary-json",
                str(summary),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = bundle.main()
            self.assertEqual(code, 0)
            self.assertTrue((root / "bundle_signal.json").exists())
            self.assertTrue((root / "bundle_signal.tsv").exists())
            self.assertTrue(summary.exists())
            summary_payload = json.loads(summary.read_text(encoding="utf-8"))
            self.assertEqual(summary_payload["consistency_check"], "passed")

    def test_main_fails_when_blocked_missing_context_under_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-bundle-") as tmp:
            root = Path(tmp)
            status = self._write_status(
                root,
                {
                    "delivery_state": "blocked_external_provider",
                    "onboarding_latest": {"block_reason": "provider_account_arrearage"},
                },
            )
            prefix = root / "bundle_signal"
            argv = [
                "project_delivery_signal_bundle.py",
                "--status-json",
                str(status),
                "--output-prefix",
                str(prefix),
                "--require-delivery-state",
                "--require-blocking-context",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = bundle.main()
            self.assertEqual(code, 2)
            self.assertFalse((root / "bundle_signal.json").exists())
            self.assertFalse((root / "bundle_signal.tsv").exists())

    def test_main_can_skip_consistency_check(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-bundle-") as tmp:
            root = Path(tmp)
            status = self._write_status(
                root,
                {
                    "delivery_state": "ready_for_replay",
                    "onboarding_latest": {},
                },
            )
            prefix = root / "bundle_signal"
            argv = [
                "project_delivery_signal_bundle.py",
                "--status-json",
                str(status),
                "--output-prefix",
                str(prefix),
                "--require-delivery-state",
                "--no-consistency-check",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = bundle.main()
            self.assertEqual(code, 0)
            self.assertTrue((root / "bundle_signal.json").exists())
            self.assertTrue((root / "bundle_signal.tsv").exists())


if __name__ == "__main__":
    unittest.main()
