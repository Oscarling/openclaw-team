from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_consistency_check.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_consistency_check", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history consistency module from {MODULE_PATH}")
provider_onboarding_history_consistency_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_consistency_check)


class ProviderOnboardingHistoryConsistencyCheckTests(unittest.TestCase):
    def _write_history(self, history: Path) -> None:
        history.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "timestamp": "2026-03-28T12:07:46",
                            "stamp": "20260328",
                            "probe_tsv": "/repo/runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv",
                            "assessment_json": "/repo/runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json",
                            "assessment_snapshot_json": "/repo/runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots/provider_handshake_assessment_gate_20260328_20260328T120746_line1.json",
                            "exit_code": 2,
                            "phase": "assess",
                            "status": "blocked",
                            "block_reason": "auth_or_access_policy_block",
                        },
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        {
                            "timestamp": "2026-03-28T12:26:50",
                            "stamp": "20260328",
                            "probe_tsv": "/repo/runtime_archives/bl100/tmp/provider_handshake_probe_gate_20260328.tsv",
                            "assessment_json": "/repo/runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json",
                            "assessment_snapshot_json": "/repo/runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots/provider_handshake_assessment_gate_20260328_20260328T122650_line2.json",
                            "exit_code": 2,
                            "phase": "assess",
                            "status": "blocked",
                            "block_reason": "mixed_with_tls_transport_failures",
                        },
                        ensure_ascii=False,
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_summary(self, history: Path, summary: Path, repo_root: Path) -> None:
        expected = provider_onboarding_history_consistency_check.build_expected_summary(
            history_path=history,
            repo_root=repo_root,
            repo_only=True,
        )
        summary.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def test_compare_summary_reports_mismatch(self) -> None:
        expected = {"entry_count": 2, "latest": {"status": "blocked"}}
        actual = {"entry_count": 1, "latest": {"status": "ready"}}
        errors = provider_onboarding_history_consistency_check.compare_summary(expected, actual)
        self.assertTrue(any("entry_count" in err for err in errors))
        self.assertTrue(any("latest" in err for err in errors))

    def test_main_passes_when_summary_matches_expected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            summary = tmp / "summary.json"
            repo_root = Path("/repo")
            self._write_history(history)
            self._write_summary(history, summary, repo_root)

            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--summary-json",
                str(summary),
                "--repo-root",
                str(repo_root),
                "--repo-only",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_consistency_check.main()
            self.assertEqual(code, 0)

    def test_main_fails_when_summary_stale(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            summary = tmp / "summary.json"
            repo_root = Path("/repo")
            self._write_history(history)
            self._write_summary(history, summary, repo_root)

            payload = json.loads(summary.read_text(encoding="utf-8"))
            payload["latest"]["block_reason"] = "auth_or_access_policy_block"
            summary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--summary-json",
                str(summary),
                "--repo-root",
                str(repo_root),
                "--repo-only",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_consistency_check.main()
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
