from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_summary.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_summary", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history summary module from {MODULE_PATH}")
provider_onboarding_history_summary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_summary)


class ProviderOnboardingHistorySummaryTests(unittest.TestCase):
    def test_build_summary_uses_latest_entry(self) -> None:
        entries = [
            {
                "timestamp": "2026-03-28T10:00:00",
                "stamp": "20260328",
                "status": "blocked",
                "block_reason": "auth_or_access_policy_block",
                "exit_code": 2,
                "note_class_counts": {"invalid_api_key": 2},
            },
            {
                "timestamp": "2026-03-28T11:00:00",
                "stamp": "20260328",
                "status": "ready",
                "block_reason": "none",
                "exit_code": 0,
                "note_class_counts": {"tls_eof": 1},
            },
        ]
        summary = provider_onboarding_history_summary.build_summary(entries, Path("history.jsonl"))
        self.assertEqual(summary["entry_count"], 2)
        self.assertEqual(summary["status_counts"]["blocked"], 1)
        self.assertEqual(summary["status_counts"]["ready"], 1)
        self.assertEqual(summary["note_class_counts"]["invalid_api_key"], 2)
        self.assertEqual(summary["note_class_counts"]["tls_eof"], 1)
        self.assertEqual(summary["latest"]["status"], "ready")
        self.assertEqual(summary["latest"]["exit_code"], 0)
        self.assertEqual(summary["latest"]["note_class_counts"], {"tls_eof": 1})

    def test_main_writes_summary_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            history.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T10:00:00",
                                "stamp": "20260328",
                                "status": "blocked",
                                "block_reason": "auth_or_access_policy_block",
                                "exit_code": 2,
                                "note_class_counts": {"invalid_api_key": 4},
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T11:00:00",
                                "stamp": "20260328",
                                "status": "blocked",
                                "block_reason": "mixed_with_tls_transport_failures",
                                "exit_code": 2,
                                "note_class_counts": {"edge_policy_1010": 3, "tls_eof": 1},
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output = tmp / "summary.json"
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--output-json",
                str(output),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_summary.main()

            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["entry_count"], 2)
            self.assertEqual(parsed["note_class_counts"]["invalid_api_key"], 4)
            self.assertEqual(parsed["note_class_counts"]["edge_policy_1010"], 3)
            self.assertEqual(parsed["latest"]["block_reason"], "mixed_with_tls_transport_failures")
            self.assertEqual(parsed["latest"]["note_class_counts"]["tls_eof"], 1)

    def test_filter_repo_entries_drops_non_repo_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            repo_root = Path(tmp_raw)
            entries = [
                {
                    "probe_tsv": str(repo_root / "runtime_archives/bl100/tmp/probe.tsv"),
                    "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/assessment.json"),
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "exit_code": 2,
                },
                {
                    "probe_tsv": "/var/folders/xx/nonrepo_probe.tsv",
                    "assessment_json": "/var/folders/xx/nonrepo_assessment.json",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "exit_code": 2,
                },
            ]
            kept, dropped = provider_onboarding_history_summary.filter_repo_entries(entries, repo_root, repo_only=True)
            self.assertEqual(len(kept), 1)
            self.assertEqual(dropped, 1)

    def test_main_repo_only_counts_only_repo_entries(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            repo_root = tmp / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            history = tmp / "history.jsonl"
            history.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T10:00:00",
                                "stamp": "20260328",
                                "status": "blocked",
                                "block_reason": "auth_or_access_policy_block",
                                "exit_code": 2,
                                "probe_tsv": str(repo_root / "runtime_archives/bl100/tmp/probe_1.tsv"),
                                "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/assessment_1.json"),
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T11:00:00",
                                "stamp": "20260328",
                                "status": "blocked",
                                "block_reason": "mixed_with_tls_transport_failures",
                                "exit_code": 2,
                                "probe_tsv": "/var/folders/xx/nonrepo_probe.tsv",
                                "assessment_json": "/var/folders/xx/nonrepo_assessment.json",
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            output = tmp / "summary.json"
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--output-json",
                str(output),
                "--repo-root",
                str(repo_root),
                "--repo-only",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_summary.main()

            self.assertEqual(code, 0)
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["entry_count"], 1)
            self.assertEqual(parsed["dropped_non_repo_entries"], 1)
            self.assertEqual(parsed["latest"]["block_reason"], "auth_or_access_policy_block")


if __name__ == "__main__":
    unittest.main()
