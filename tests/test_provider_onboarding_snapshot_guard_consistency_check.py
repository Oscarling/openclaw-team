from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_consistency_check.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_consistency_check", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding snapshot guard consistency module from {MODULE_PATH}")
provider_onboarding_snapshot_guard_consistency_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_snapshot_guard_consistency_check)


class ProviderOnboardingSnapshotGuardConsistencyCheckTests(unittest.TestCase):
    def _summary_payload(self, repo_root: Path) -> dict:
        return {
            "history_jsonl": str(repo_root / "runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl"),
            "assess_entry_count": 2,
            "assess_rows_with_snapshot": 2,
            "assess_rows_with_snapshot_guard_match": 1,
            "assess_rows_with_snapshot_guard_mismatch": 1,
            "assess_rows_with_snapshot_guard_unverified": 0,
            "assess_snapshot_guard_match_percent": 50.0,
            "assess_snapshot_guard_mismatch_reason_counts": {"block_reason": 1},
        }

    def _report_payload(self, repo_root: Path) -> dict:
        return {
            "history_jsonl": str(repo_root / "runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl"),
            "repo_only": True,
            "assess_entry_count": 2,
            "evaluated_assess_rows": 2,
            "guard_match_rows": 1,
            "guard_mismatch_rows": 1,
            "guard_unverified_rows": 0,
            "guard_skipped_rows": 0,
            "guard_match_percent": 50.0,
            "reason_counts": {
                "guard_match": 1,
                "guard_mismatch_block_reason": 1,
            },
            "non_match_rows": [
                {
                    "history_line": 1,
                    "timestamp": "2026-03-28T12:07:46",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "assessment_json": str(repo_root / "runtime_archives/bl100/tmp/provider_handshake_assessment_gate_20260328.json"),
                    "assessment_snapshot_json": str(
                        repo_root
                        / "runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots/provider_handshake_assessment_gate_20260328_20260328T120746_line1.json"
                    ),
                    "reason": "guard_mismatch_block_reason",
                    "detail": {
                        "entry_block_reason": "auth_or_access_policy_block",
                        "snapshot_block_reason": "mixed_with_tls_transport_failures",
                    },
                }
            ],
        }

    def test_compare_summary_vs_guard_report_passes_on_match(self) -> None:
        errors = provider_onboarding_snapshot_guard_consistency_check.compare_summary_vs_guard_report(
            self._summary_payload(REPO_ROOT),
            self._report_payload(REPO_ROOT),
        )
        self.assertEqual(errors, [])

    def test_compare_summary_vs_guard_report_detects_mismatch(self) -> None:
        summary = self._summary_payload(REPO_ROOT)
        summary["assess_rows_with_snapshot_guard_match"] = 2
        errors = provider_onboarding_snapshot_guard_consistency_check.compare_summary_vs_guard_report(
            summary,
            self._report_payload(REPO_ROOT),
        )
        self.assertTrue(any("assess_rows_with_snapshot_guard_match" in err for err in errors))

    def test_compare_summary_vs_guard_report_detects_history_jsonl_mismatch(self) -> None:
        summary = self._summary_payload(REPO_ROOT)
        summary["history_jsonl"] = str(REPO_ROOT / "runtime_archives/bl100/tmp/other_history.jsonl")
        errors = provider_onboarding_snapshot_guard_consistency_check.compare_summary_vs_guard_report(
            summary,
            self._report_payload(REPO_ROOT),
        )
        self.assertTrue(any("history_jsonl" in err for err in errors))

    def test_main_passes_when_files_match(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            summary_path = tmp / "summary.json"
            report_path = tmp / "report.json"
            summary_path.write_text(json.dumps(self._summary_payload(tmp), ensure_ascii=False), encoding="utf-8")
            report_path.write_text(json.dumps(self._report_payload(tmp), ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--summary-json",
                str(summary_path),
                "--guard-report-json",
                str(report_path),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_consistency_check.main()
            self.assertEqual(code, 0)

    def test_main_fails_when_files_diverge(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            summary_path = tmp / "summary.json"
            report_path = tmp / "report.json"
            summary = self._summary_payload(tmp)
            summary["assess_snapshot_guard_mismatch_reason_counts"] = {"status": 1}
            summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
            report_path.write_text(json.dumps(self._report_payload(tmp), ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--summary-json",
                str(summary_path),
                "--guard-report-json",
                str(report_path),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_consistency_check.main()
            self.assertEqual(code, 2)

    def test_main_fails_when_report_schema_invalid(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            summary_path = tmp / "summary.json"
            report_path = tmp / "report.json"
            payload = self._report_payload(tmp)
            payload["reason_counts"]["unknown_reason"] = 1
            summary_path.write_text(json.dumps(self._summary_payload(tmp), ensure_ascii=False), encoding="utf-8")
            report_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--summary-json",
                str(summary_path),
                "--guard-report-json",
                str(report_path),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_consistency_check.main()
            self.assertEqual(code, 2)

    def test_main_fails_when_summary_schema_invalid(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-consistency-") as tmp_raw:
            tmp = Path(tmp_raw)
            summary_path = tmp / "summary.json"
            report_path = tmp / "report.json"
            summary = self._summary_payload(tmp)
            summary["assess_snapshot_guard_mismatch_reason_counts"] = {"unexpected": 1}
            summary_path.write_text(json.dumps(summary, ensure_ascii=False), encoding="utf-8")
            report_path.write_text(json.dumps(self._report_payload(tmp), ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--summary-json",
                str(summary_path),
                "--guard-report-json",
                str(report_path),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_consistency_check.main()
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
