from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_gate.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_gate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding gate module from {MODULE_PATH}")
provider_onboarding_gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_gate)


class ProviderOnboardingGateTests(unittest.TestCase):
    def test_main_stops_when_probe_fails(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str]):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 3, stdout="", stderr="probe failed")

        with tempfile.TemporaryDirectory(prefix="provider-onboarding-gate-") as tmp:
            argv = [
                str(MODULE_PATH),
                "--output-dir",
                tmp,
                "--stamp",
                "20260328",
            ]
            with mock.patch.object(provider_onboarding_gate, "run_command", side_effect=fake_run):
                with mock.patch.object(sys, "argv", argv):
                    code = provider_onboarding_gate.main()

        self.assertEqual(code, 3)
        self.assertEqual(len(calls), 1)
        self.assertIn("provider_handshake_probe.py", calls[0][1])

    def test_main_returns_assessment_code(self) -> None:
        calls: list[list[str]] = []

        def fake_run(cmd: list[str]):
            calls.append(cmd)
            if "provider_handshake_probe.py" in cmd[1]:
                return subprocess.CompletedProcess(cmd, 0, stdout="probe.tsv", stderr="")
            return subprocess.CompletedProcess(cmd, 2, stdout="summary.json", stderr="blocked")

        with tempfile.TemporaryDirectory(prefix="provider-onboarding-gate-") as tmp:
            argv = [
                str(MODULE_PATH),
                "--output-dir",
                tmp,
                "--stamp",
                "20260328",
                "--probe-all-keys",
                "--require-ready",
                "--key-file",
                "/tmp/k1",
                "--endpoint",
                "https://example.invalid/v1/responses",
            ]
            with mock.patch.object(provider_onboarding_gate, "run_command", side_effect=fake_run):
                with mock.patch.object(sys, "argv", argv):
                    code = provider_onboarding_gate.main()

        self.assertEqual(code, 2)
        self.assertEqual(len(calls), 2)
        probe_cmd = calls[0]
        assess_cmd = calls[1]
        self.assertIn("provider_handshake_probe.py", probe_cmd[1])
        self.assertIn("--probe-all-keys", probe_cmd)
        self.assertIn("--key-file", probe_cmd)
        self.assertIn("--endpoint", probe_cmd)
        self.assertIn("provider_handshake_assess.py", assess_cmd[1])
        self.assertIn("--require-ready", assess_cmd)


if __name__ == "__main__":
    unittest.main()
