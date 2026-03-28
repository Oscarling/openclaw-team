from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_report_validate.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_report_validate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load snapshot guard report validate module from {MODULE_PATH}")
provider_onboarding_snapshot_guard_report_validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_snapshot_guard_report_validate)


class ProviderOnboardingSnapshotGuardReportValidateTests(unittest.TestCase):
    def _valid_report(self, repo_root: Path) -> dict:
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

    def test_validate_report_passes_for_well_formed_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            report = self._valid_report(tmp)
            errors = provider_onboarding_snapshot_guard_report_validate.validate_report(
                report,
                repo_root=tmp,
                require_repo_paths=False,
            )
            self.assertEqual(errors, [])

    def test_validate_report_detects_inconsistent_totals(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            report = self._valid_report(tmp)
            report["guard_match_rows"] = 2
            errors = provider_onboarding_snapshot_guard_report_validate.validate_report(
                report,
                repo_root=tmp,
                require_repo_paths=False,
            )
            self.assertTrue(any("evaluated_assess_rows must equal" in err for err in errors))

    def test_main_passes_with_repo_path_enforcement(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            report = self._valid_report(tmp)
            report_json = tmp / "report.json"
            report_json.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--report-json",
                str(report_json),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_report_validate.main()
            self.assertEqual(code, 0)

    def test_main_fails_for_non_repo_path_when_required(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            report = self._valid_report(tmp)
            report["non_match_rows"][0]["assessment_snapshot_json"] = "/var/folders/nonrepo_snapshot.json"
            report_json = tmp / "report.json"
            report_json.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--report-json",
                str(report_json),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_report_validate.main()
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
