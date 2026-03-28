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
        self.assertEqual(summary["note_class_counts"]["invalid_api_key"], 1)
        self.assertEqual(summary["note_class_counts"]["edge_policy_1010"], 1)

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
        self.assertEqual(summary["retry_attempt_total"], 0)
        self.assertEqual(summary["rows_with_retry"], 0)
        self.assertEqual(summary["retry_reason_counts"], {})

    def test_build_summary_collects_retry_metrics(self) -> None:
        rows = [
            {
                "endpoint": "https://example.invalid/v1/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "401",
                "note": "key=***abc123; invalid",
                "retry_count": "0",
                "retry_reasons": "",
            },
            {
                "endpoint": "https://example.invalid/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "200",
                "note": "key=***abc123; api_like=true; ok",
                "retry_count": "2",
                "retry_reasons": "timeout,http_5xx",
                "api_like": "1",
            },
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["retry_attempt_total"], 2)
        self.assertEqual(summary["rows_with_retry"], 1)
        self.assertEqual(summary["retry_reason_counts"]["timeout"], 1)
        self.assertEqual(summary["retry_reason_counts"]["http_5xx"], 1)

    def test_build_summary_blocks_non_api_success_payload(self) -> None:
        rows = [
            {
                "endpoint": "http://example.invalid/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "200",
                "note": "key=***tailok; api_like=false; content_type=text/html; <!doctype html>",
            }
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["block_reason"], "non_api_success_payload")
        self.assertEqual(summary["success_row_count"], 0)
        self.assertEqual(summary["note_class_counts"]["non_api_success_payload"], 1)

    def test_build_summary_blocks_non_api_success_payload_from_column(self) -> None:
        rows = [
            {
                "endpoint": "http://example.invalid/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "200",
                "note": "key=***tailok; ok",
                "api_like": "0",
            }
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["block_reason"], "non_api_success_payload")
        self.assertEqual(summary["success_row_count"], 0)

    def test_build_summary_mixed_with_tls_transport_failures(self) -> None:
        rows = [
            {
                "endpoint": "https://aixj.vip/v1/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "401",
                "note": 'key=***abc123; {"code":"INVALID_API_KEY"}',
            },
            {
                "endpoint": "https://fast.vpsairobot.com/responses",
                "model": "gpt-5-codex",
                "probe": "ping",
                "http_code": "000",
                "note": "key=***abc123; <urlopen error EOF occurred in violation of protocol (_ssl.c:1129)>",
            },
        ]
        summary = provider_handshake_assess.build_summary(rows, Path("dummy.tsv"))
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["block_reason"], "mixed_with_tls_transport_failures")
        self.assertEqual(summary["note_class_counts"]["tls_eof"], 1)

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
