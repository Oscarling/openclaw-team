from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_handshake_probe.py"
SPEC = importlib.util.spec_from_file_location("provider_handshake_probe", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider handshake probe module from {MODULE_PATH}")
provider_handshake_probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_handshake_probe)


class ProviderHandshakeProbeTests(unittest.TestCase):
    def test_extract_keys_deduplicates(self) -> None:
        text = "abc sk-aaaaabbbbbcccccdddddeeeee11111 xyz sk-aaaaabbbbbcccccdddddeeeee11111"
        self.assertEqual(
            provider_handshake_probe.extract_keys(text),
            ["sk-aaaaabbbbbcccccdddddeeeee11111"],
        )

    def test_build_probe_rows_missing_key(self) -> None:
        rows = provider_handshake_probe.build_probe_rows(
            keys=[],
            endpoints=["https://example.invalid/v1/responses", "https://example.invalid/responses"],
            model="gpt-5-codex",
            input_text="ping",
            timeout=10,
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][3], "000")
        self.assertEqual(rows[0][4], "missing_key")

    def test_build_probe_rows_masks_key_tail(self) -> None:
        seen = []

        def fake_probe(endpoint: str, key: str, model: str, input_text: str, timeout: int):
            seen.append((endpoint, key, model, input_text, timeout))
            return "401", '{"code":"INVALID_API_KEY"}'

        rows = provider_handshake_probe.build_probe_rows(
            keys=["sk-1234567890abcdefghijklmnopqrstuvwxyzABCDEF"],
            endpoints=["https://example.invalid/v1/responses"],
            model="gpt-5-codex",
            input_text="ping",
            timeout=12,
            probe_func=fake_probe,
        )

        self.assertEqual(len(rows), 1)
        self.assertIn("key=***ABCDEF", rows[0][4])
        self.assertEqual(seen[0][4], 12)

    def test_count_success_codes(self) -> None:
        rows = [
            ("a", "m", "p", "401", "x"),
            ("b", "m", "p", "200", "x"),
            ("c", "m", "p", "204", "x"),
            ("d", "m", "p", "000", "x"),
        ]
        self.assertEqual(provider_handshake_probe.count_success_codes(rows), 2)

    def test_main_require_success_returns_nonzero_when_no_2xx(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-handshake-probe-") as tmp:
            output = Path(tmp) / "probe.tsv"
            missing = Path(tmp) / "missing_key_file"
            argv = [
                str(MODULE_PATH),
                "--key-file",
                str(missing),
                "--output",
                str(output),
                "--require-success",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_handshake_probe.main()

            self.assertEqual(code, 2)
            self.assertTrue(output.exists())
            lines = output.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(lines), 2)
            self.assertIn("missing_key", lines[1])

    def test_main_require_success_passes_when_probe_has_2xx(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-handshake-probe-") as tmp:
            output = Path(tmp) / "probe.tsv"
            key_file = Path(tmp) / "keys.txt"
            key_file.write_text("sk-aaaaaaaaaabbbbbbbbbbccccccccccdddddddddd", encoding="utf-8")

            def fake_probe(endpoint: str, key: str, model: str, input_text: str, timeout: int):
                return "200", "ok"

            argv = [
                str(MODULE_PATH),
                "--key-file",
                str(key_file),
                "--endpoint",
                "https://example.invalid/v1/responses",
                "--output",
                str(output),
                "--require-success",
            ]
            with mock.patch.object(provider_handshake_probe, "probe_once", side_effect=fake_probe):
                with mock.patch.object(sys, "argv", argv):
                    code = provider_handshake_probe.main()

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            content = output.read_text(encoding="utf-8")
            self.assertIn("\t200\t", content)


if __name__ == "__main__":
    unittest.main()
