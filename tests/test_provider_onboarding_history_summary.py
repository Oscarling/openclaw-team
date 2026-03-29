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
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            snap1 = tmp / "snap1.json"
            snap1.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "http_code_counts": {"403": 2},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            snap2 = tmp / "snap2.json"
            snap2.write_text(
                json.dumps(
                    {
                        "status": "ready",
                        "block_reason": "none",
                        "http_code_counts": {"200": 1},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            entries = [
                {
                    "timestamp": "2026-03-28T10:00:00",
                    "stamp": "20260328",
                    "phase": "assess",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "exit_code": 2,
                    "http_code_counts": {"403": 2},
                    "note_class_counts": {"invalid_api_key": 2},
                    "assessment_snapshot_json": str(snap1),
                },
                {
                    "timestamp": "2026-03-28T11:00:00",
                    "stamp": "20260328",
                    "phase": "assess",
                    "status": "ready",
                    "block_reason": "none",
                    "exit_code": 0,
                    "http_code_counts": {"200": 1},
                    "note_class_counts": {"tls_eof": 1},
                    "assessment_snapshot_json": str(snap2),
                },
            ]
            summary = provider_onboarding_history_summary.build_summary(entries, Path("history.jsonl"))
            self.assertEqual(summary["entry_count"], 2)
            self.assertEqual(summary["status_counts"]["blocked"], 1)
            self.assertEqual(summary["status_counts"]["ready"], 1)
            self.assertEqual(summary["note_class_counts"]["invalid_api_key"], 2)
            self.assertEqual(summary["note_class_counts"]["tls_eof"], 1)
            self.assertEqual(summary["rows_with_note_class_counts"], 2)
            self.assertEqual(summary["rows_missing_note_class_counts"], 0)
            self.assertEqual(summary["note_signal_coverage_percent"], 100.0)
            self.assertEqual(summary["assess_entry_count"], 2)
            self.assertEqual(summary["assess_rows_with_snapshot"], 2)
            self.assertEqual(summary["assess_rows_missing_snapshot"], 0)
            self.assertEqual(summary["assess_snapshot_coverage_percent"], 100.0)
            self.assertEqual(summary["assess_rows_with_snapshot_guard_match"], 2)
            self.assertEqual(summary["assess_rows_with_snapshot_guard_mismatch"], 0)
            self.assertEqual(summary["assess_rows_with_snapshot_guard_unverified"], 0)
            self.assertEqual(summary["assess_snapshot_guard_match_percent"], 100.0)
            self.assertEqual(summary["assess_snapshot_guard_mismatch_reason_counts"], {})
            self.assertEqual(summary["latest"]["status"], "ready")
            self.assertEqual(summary["latest"]["exit_code"], 0)
            self.assertEqual(summary["latest"]["note_class_counts"], {"tls_eof": 1})
            self.assertEqual(summary["latest"]["assessment_snapshot_json"], str(snap2))

    def test_main_writes_summary_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            (tmp / "snap1.json").write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "http_code_counts": {"403": 4},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (tmp / "snap2.json").write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            history = tmp / "history.jsonl"
            history.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T10:00:00",
                                "stamp": "20260328",
                                "phase": "assess",
                                "status": "blocked",
                                "block_reason": "auth_or_access_policy_block",
                                "exit_code": 2,
                                "http_code_counts": {"403": 4},
                                "note_class_counts": {"invalid_api_key": 4},
                                "assessment_snapshot_json": str(tmp / "snap1.json"),
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T11:00:00",
                                "stamp": "20260328",
                                "phase": "assess",
                                "status": "blocked",
                                "block_reason": "mixed_with_tls_transport_failures",
                                "exit_code": 2,
                                "http_code_counts": {"000": 1, "401": 4, "403": 3},
                                "note_class_counts": {"edge_policy_1010": 3, "tls_eof": 1},
                                "assessment_snapshot_json": str(tmp / "snap2.json"),
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
            self.assertEqual(parsed["rows_with_note_class_counts"], 2)
            self.assertEqual(parsed["rows_missing_note_class_counts"], 0)
            self.assertEqual(parsed["note_signal_coverage_percent"], 100.0)
            self.assertEqual(parsed["assess_entry_count"], 2)
            self.assertEqual(parsed["assess_rows_with_snapshot"], 2)
            self.assertEqual(parsed["assess_rows_missing_snapshot"], 0)
            self.assertEqual(parsed["assess_snapshot_coverage_percent"], 100.0)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_match"], 2)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_mismatch"], 0)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_unverified"], 0)
            self.assertEqual(parsed["assess_snapshot_guard_match_percent"], 100.0)
            self.assertEqual(parsed["assess_snapshot_guard_mismatch_reason_counts"], {})
            self.assertEqual(parsed["latest"]["block_reason"], "mixed_with_tls_transport_failures")
            self.assertEqual(parsed["latest"]["note_class_counts"]["tls_eof"], 1)
            self.assertEqual(parsed["latest"]["assessment_snapshot_json"], str(tmp / "snap2.json"))

    def test_filter_repo_entries_drops_non_repo_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            repo_root = Path(tmp_raw)
            entries = [
                {
                    "phase": "assess",
                    "probe_tsv": str(repo_root / "runtime_archives/bl100/tmp/probe.tsv"),
                    "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/assessment.json"),
                    "assessment_snapshot_json": str(repo_root / "runtime_archives/bl100/tmp/snapshot.json"),
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "exit_code": 2,
                },
                {
                    "phase": "assess",
                    "probe_tsv": "/var/folders/xx/nonrepo_probe.tsv",
                    "assessment_json": "/var/folders/xx/nonrepo_assessment.json",
                    "assessment_snapshot_json": "/var/folders/xx/nonrepo_snapshot.json",
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
                                "phase": "assess",
                                "status": "blocked",
                                "block_reason": "auth_or_access_policy_block",
                                "exit_code": 2,
                                "probe_tsv": str(repo_root / "runtime_archives/bl100/tmp/probe_1.tsv"),
                                "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/assessment_1.json"),
                                "assessment_snapshot_json": str(repo_root / "runtime_archives/bl100/tmp/snapshot_1.json"),
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "timestamp": "2026-03-28T11:00:00",
                                "stamp": "20260328",
                                "phase": "assess",
                                "status": "blocked",
                                "block_reason": "mixed_with_tls_transport_failures",
                                "exit_code": 2,
                                "probe_tsv": "/var/folders/xx/nonrepo_probe.tsv",
                                "assessment_json": "/var/folders/xx/nonrepo_assessment.json",
                                "assessment_snapshot_json": "/var/folders/xx/nonrepo_snapshot.json",
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
            self.assertEqual(parsed["rows_with_note_class_counts"], 0)
            self.assertEqual(parsed["rows_missing_note_class_counts"], 1)
            self.assertEqual(parsed["note_signal_coverage_percent"], 0.0)
            self.assertEqual(parsed["assess_entry_count"], 1)
            self.assertEqual(parsed["assess_rows_with_snapshot"], 1)
            self.assertEqual(parsed["assess_rows_missing_snapshot"], 0)
            self.assertEqual(parsed["assess_snapshot_coverage_percent"], 100.0)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_match"], 0)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_mismatch"], 0)
            self.assertEqual(parsed["assess_rows_with_snapshot_guard_unverified"], 1)
            self.assertEqual(parsed["assess_snapshot_guard_match_percent"], 0.0)
            self.assertEqual(parsed["assess_snapshot_guard_mismatch_reason_counts"], {})
            self.assertEqual(parsed["latest"]["block_reason"], "auth_or_access_policy_block")

    def test_filter_repo_entries_drops_assess_row_missing_repo_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            repo_root = Path(tmp_raw)
            entries = [
                {
                    "phase": "assess",
                    "probe_tsv": str(repo_root / "runtime_archives/bl100/tmp/probe.tsv"),
                    "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/assessment.json"),
                    "assessment_snapshot_json": "/var/folders/xx/nonrepo_snapshot.json",
                }
            ]
            kept, dropped = provider_onboarding_history_summary.filter_repo_entries(entries, repo_root, repo_only=True)
            self.assertEqual(len(kept), 0)
            self.assertEqual(dropped, 1)

    def test_build_summary_counts_snapshot_guard_mismatch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            snapshot = tmp / "snap_mismatch.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            entries = [
                {
                    "timestamp": "2026-03-28T10:00:00",
                    "stamp": "20260328",
                    "phase": "assess",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"403": 4},
                    "assessment_snapshot_json": str(snapshot),
                }
            ]
            summary = provider_onboarding_history_summary.build_summary(entries, Path("history.jsonl"))
            self.assertEqual(summary["assess_rows_with_snapshot_guard_match"], 0)
            self.assertEqual(summary["assess_rows_with_snapshot_guard_mismatch"], 1)
            self.assertEqual(summary["assess_rows_with_snapshot_guard_unverified"], 0)
            self.assertEqual(summary["assess_snapshot_guard_match_percent"], 0.0)
            self.assertEqual(summary["assess_snapshot_guard_mismatch_reason_counts"], {"block_reason": 1})

    def test_build_summary_counts_http_code_guard_mismatch_reason(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-") as tmp_raw:
            tmp = Path(tmp_raw)
            snapshot = tmp / "snap_http_mismatch.json"
            snapshot.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            entries = [
                {
                    "timestamp": "2026-03-28T10:00:00",
                    "stamp": "20260328",
                    "phase": "assess",
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"401": 4, "403": 4},
                    "assessment_snapshot_json": str(snapshot),
                }
            ]
            summary = provider_onboarding_history_summary.build_summary(entries, Path("history.jsonl"))
            self.assertEqual(summary["assess_snapshot_guard_mismatch_reason_counts"], {"http_code_counts": 1})


if __name__ == "__main__":
    unittest.main()
