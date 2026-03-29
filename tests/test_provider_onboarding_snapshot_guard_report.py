from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding snapshot guard report module from {MODULE_PATH}")
provider_onboarding_snapshot_guard_report = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_snapshot_guard_report)


class ProviderOnboardingSnapshotGuardReportTests(unittest.TestCase):
    def test_build_snapshot_guard_report_counts_match_mismatch_and_unverified(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-") as tmp_raw:
            tmp = Path(tmp_raw)
            snap_match = tmp / "snap_match.json"
            snap_match.write_text(
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
            snap_mismatch = tmp / "snap_mismatch.json"
            snap_mismatch.write_text(
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

            rows = [
                {
                    "phase": "assess",
                    "timestamp": "2026-03-28T12:07:46",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"403": 4},
                    "assessment_snapshot_json": str(snap_match),
                },
                {
                    "phase": "assess",
                    "timestamp": "2026-03-28T12:26:50",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"403": 4},
                    "assessment_snapshot_json": str(snap_mismatch),
                },
                {
                    "phase": "assess",
                    "timestamp": "2026-03-28T12:30:00",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                },
                {
                    "phase": "probe",
                    "timestamp": "2026-03-28T12:31:00",
                    "stamp": "20260328",
                    "status": "probe_failed",
                    "block_reason": "probe_command_failed",
                },
            ]
            report = provider_onboarding_snapshot_guard_report.build_snapshot_guard_report(
                rows,
                history_path=tmp / "history.jsonl",
                repo_root=tmp,
                repo_only=False,
            )
            self.assertEqual(report["assess_entry_count"], 3)
            self.assertEqual(report["evaluated_assess_rows"], 3)
            self.assertEqual(report["guard_match_rows"], 1)
            self.assertEqual(report["guard_mismatch_rows"], 1)
            self.assertEqual(report["guard_unverified_rows"], 1)
            self.assertEqual(report["guard_match_percent"], 33.33)
            self.assertEqual(report["reason_counts"]["guard_match"], 1)
            self.assertEqual(report["reason_counts"]["guard_mismatch_block_reason"], 1)
            self.assertEqual(report["reason_counts"]["snapshot_missing"], 1)
            self.assertEqual(len(report["non_match_rows"]), 2)

    def test_build_snapshot_guard_report_repo_only_marks_non_repo_snapshot(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-") as tmp_raw:
            tmp = Path(tmp_raw)
            row = {
                "phase": "assess",
                "timestamp": "2026-03-28T12:26:50",
                "stamp": "20260328",
                "status": "blocked",
                "block_reason": "mixed_with_tls_transport_failures",
                "probe_tsv": str(tmp / "probe.tsv"),
                "assessment_json": str(tmp / "assessment.json"),
                "assessment_snapshot_json": "/var/folders/nonrepo_snapshot.json",
            }
            report = provider_onboarding_snapshot_guard_report.build_snapshot_guard_report(
                [row],
                history_path=tmp / "history.jsonl",
                repo_root=tmp,
                repo_only=True,
            )
            self.assertEqual(report["guard_unverified_rows"], 1)
            self.assertEqual(report["reason_counts"]["snapshot_not_repo_scoped"], 1)
            self.assertEqual(report["non_match_rows"][0]["reason"], "snapshot_not_repo_scoped")

    def test_main_writes_report_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-") as tmp_raw:
            tmp = Path(tmp_raw)
            snapshot = tmp / "snapshot.json"
            snapshot.write_text(
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
            history = tmp / "history.jsonl"
            history.write_text(
                json.dumps(
                    {
                        "phase": "assess",
                        "timestamp": "2026-03-28T12:07:46",
                        "stamp": "20260328",
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "http_code_counts": {"403": 4},
                        "assessment_snapshot_json": str(snapshot),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            output = tmp / "guard_report.json"
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--output-json",
                str(output),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_report.main()
            self.assertEqual(code, 0)
            self.assertTrue(output.exists())
            parsed = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(parsed["guard_match_rows"], 1)
            self.assertEqual(parsed["guard_mismatch_rows"], 0)


if __name__ == "__main__":
    unittest.main()
