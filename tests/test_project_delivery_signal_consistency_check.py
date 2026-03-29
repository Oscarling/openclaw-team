from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import project_delivery_signal
from scripts import project_delivery_signal_consistency_check as check


class ProjectDeliverySignalConsistencyCheckTests(unittest.TestCase):
    def _write_status_and_signal(self, root: Path) -> tuple[Path, Path, Path]:
        status_path = root / "status.json"
        signal_json_path = root / "signal.json"
        signal_tsv_path = root / "signal.tsv"

        status_payload = {
            "delivery_state": "blocked_external_provider",
            "blocking_signal": {
                "stage": "handshake_gate",
                "reason": "provider_account_arrearage",
            },
            "onboarding_latest": {
                "block_reason": "provider_account_arrearage",
                "timestamp": "2026-03-29T14:48:40",
            },
        }
        signal_payload = project_delivery_signal.build_signal(status_payload)
        status_path.write_text(json.dumps(status_payload), encoding="utf-8")
        signal_json_path.write_text(json.dumps(signal_payload), encoding="utf-8")
        signal_tsv_path.write_text(
            project_delivery_signal._render_tsv(signal_payload, with_header=True),
            encoding="utf-8",
        )
        return status_path, signal_json_path, signal_tsv_path

    def test_main_passes_when_signal_json_and_tsv_match(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-check-") as tmp:
            root = Path(tmp)
            status_path, signal_json_path, signal_tsv_path = self._write_status_and_signal(root)
            argv = [
                "project_delivery_signal_consistency_check.py",
                "--status-json",
                str(status_path),
                "--signal-json",
                str(signal_json_path),
                "--signal-tsv",
                str(signal_tsv_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = check.main()
            self.assertEqual(code, 0)

    def test_main_fails_when_signal_json_mismatches(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-check-") as tmp:
            root = Path(tmp)
            status_path, signal_json_path, signal_tsv_path = self._write_status_and_signal(root)
            drifted = json.loads(signal_json_path.read_text(encoding="utf-8"))
            drifted["blocking_reason"] = "drifted"
            signal_json_path.write_text(json.dumps(drifted), encoding="utf-8")

            argv = [
                "project_delivery_signal_consistency_check.py",
                "--status-json",
                str(status_path),
                "--signal-json",
                str(signal_json_path),
                "--signal-tsv",
                str(signal_tsv_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = check.main()
            self.assertEqual(code, 2)

    def test_main_fails_when_signal_tsv_mismatches(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-check-") as tmp:
            root = Path(tmp)
            status_path, signal_json_path, signal_tsv_path = self._write_status_and_signal(root)
            signal_tsv_path.write_text(
                "delivery_state\tblocking_stage\tblocking_reason\tblocking_action\tonboarding_block_reason\tonboarding_timestamp\n"
                "blocked_external_provider\thandshake_gate\tdrifted\tpause\tprovider_account_arrearage\t2026-03-29T14:48:40\n",
                encoding="utf-8",
            )

            argv = [
                "project_delivery_signal_consistency_check.py",
                "--status-json",
                str(status_path),
                "--signal-json",
                str(signal_json_path),
                "--signal-tsv",
                str(signal_tsv_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = check.main()
            self.assertEqual(code, 2)

    def test_main_requires_at_least_one_signal_artifact(self) -> None:
        with tempfile.TemporaryDirectory(prefix="project-delivery-signal-check-") as tmp:
            root = Path(tmp)
            status_path, _, _ = self._write_status_and_signal(root)
            argv = [
                "project_delivery_signal_consistency_check.py",
                "--status-json",
                str(status_path),
            ]
            with mock.patch.object(sys, "argv", argv):
                with self.assertRaises(RuntimeError):
                    check.main()


if __name__ == "__main__":
    unittest.main()
