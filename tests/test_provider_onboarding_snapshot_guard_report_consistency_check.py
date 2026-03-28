from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report_consistency_check.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report_consistency_check", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load snapshot guard report consistency module from {MODULE_PATH}")
provider_onboarding_snapshot_guard_report_consistency_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_snapshot_guard_report_consistency_check)


class ProviderOnboardingSnapshotGuardReportConsistencyCheckTests(unittest.TestCase):
    def _write_history_and_snapshot(self, tmp: Path) -> Path:
        snapshot = tmp / "snapshot.json"
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
        history = tmp / "history.jsonl"
        history.write_text(
            json.dumps(
                {
                    "phase": "assess",
                    "timestamp": "2026-03-28T12:07:46",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"401": 4, "403": 4},
                    "assessment_snapshot_json": str(snapshot),
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        return history

    def test_compare_report_detects_mismatch(self) -> None:
        expected = {"guard_match_rows": 1}
        actual = {"guard_match_rows": 0}
        errors = provider_onboarding_snapshot_guard_report_consistency_check.compare_report(expected, actual)
        self.assertTrue(any("guard_match_rows" in err for err in errors))

    def test_main_passes_when_report_matches_history(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-report-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = self._write_history_and_snapshot(tmp)
            report = provider_onboarding_snapshot_guard_report_consistency_check.build_expected_report(
                history_path=history,
                repo_root=tmp,
                repo_only=False,
            )
            report_json = tmp / "report.json"
            report_json.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--report-json",
                str(report_json),
                "--repo-root",
                str(tmp),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_report_consistency_check.main()
            self.assertEqual(code, 0)

    def test_main_fails_when_report_is_stale(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-report-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = self._write_history_and_snapshot(tmp)
            report = provider_onboarding_snapshot_guard_report_consistency_check.build_expected_report(
                history_path=history,
                repo_root=tmp,
                repo_only=False,
            )
            report["guard_mismatch_rows"] = 0
            report_json = tmp / "report.json"
            report_json.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--report-json",
                str(report_json),
                "--repo-root",
                str(tmp),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_report_consistency_check.main()
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
