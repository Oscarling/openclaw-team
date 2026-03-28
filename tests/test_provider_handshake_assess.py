from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_handshake_assess.py"
SPEC = importlib.util.spec_from_file_location("provider_handshake_assess", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider handshake assess module from {MODULE_PATH}")
provider_handshake_assess = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_handshake_assess)


class ProviderHandshakeAssessTests(unittest.TestCase):
    def _write_probe_tsv(self, tmp: Path, body_lines: list[str]) -> Path:
        path = tmp / "probe.tsv"
        lines = ["endpoint\tmodel\tprobe\thttp_code\tnote"] + body_lines
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def test_build_summary_blocked_auth_or_access(self) -> None:
        rows = [
            {
                "endpoint": "https://aixj.vip/v1/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "401",
                "note": 'key=***abc123; {"code":"INVALID_API_KEY"}',
            },
            {
                "endpoint": "https://fast.vpsairobot.com/v1/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "403",
                "note": "key=***abc123; error code: 1010",
            },
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["block_reason"], "auth_or_access_policy_block")
        self.assertEqual(summary["success_row_count"], 0)
        self.assertEqual(summary["key_tails"], ["abc123"])

    def test_build_summary_ready_with_2xx(self) -> None:
        rows = [
            {
                "endpoint": "https://example.invalid/v1/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "200",
                "note": "key=***tailok; ok",
            }
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["block_reason"], "none")
        self.assertEqual(summary["success_row_count"], 1)

    def test_main_require_ready_returns_nonzero_for_blocked(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-handshake-assess-") as tmp_raw:
            tmp = Path(tmp_raw)
            probe = self._write_probe_tsv(
                tmp,
                [
                    "https://aixj.vip/v1/responses\tgpt-5-codex\tping\t401\tkey=***abc123; invalid",
                    "https://fast.vpsairobot.com/v1/responses\tgpt-5-codex\tping\t403\tkey=***abc123; 1010",
                ],
            )
            out = tmp / "summary.json"
            argv = [
                str(MODULE_PATH),
                "--probe-tsv",
                str(probe),
                "--output-json",
                str(out),
                "--require-ready",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_handshake_assess.main()

            self.assertEqual(code, 2)
            self.assertTrue(out.exists())
            content = out.read_text(encoding="utf-8")
            self.assertIn('"status": "blocked"', content)

    def test_main_require_ready_passes_for_ready(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-handshake-assess-") as tmp_raw:
            tmp = Path(tmp_raw)
            probe = self._write_probe_tsv(
                tmp,
                [
                    "https://example.invalid/v1/responses\tgpt-5-codex\tping\t200\tkey=***good01; ok",
                ],
            )
            out = tmp / "summary.json"
            argv = [
                str(MODULE_PATH),
                "--probe-tsv",
                str(probe),
                "--output-json",
                str(out),
                "--require-ready",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_handshake_assess.main()

            self.assertEqual(code, 0)
            self.assertTrue(out.exists())
            content = out.read_text(encoding="utf-8")
            self.assertIn('"status": "ready"', content)


if __name__ == "__main__":
    unittest.main()
