from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_snapshot_guard_summary_validate.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_snapshot_guard_summary_validate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load snapshot guard summary validate module from {MODULE_PATH}")
provider_onboarding_snapshot_guard_summary_validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_snapshot_guard_summary_validate)


class ProviderOnboardingSnapshotGuardSummaryValidateTests(unittest.TestCase):
    def _valid_summary(self) -> dict:
        return {
            "history_jsonl": "runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
            "assess_entry_count": 2,
            "assess_rows_with_snapshot": 2,
            "assess_rows_with_snapshot_guard_match": 1,
            "assess_rows_with_snapshot_guard_mismatch": 1,
            "assess_rows_with_snapshot_guard_unverified": 0,
            "assess_snapshot_guard_match_percent": 50.0,
            "assess_snapshot_guard_mismatch_reason_counts": {"block_reason": 1},
        }

    def test_validate_summary_passes_for_well_formed_payload(self) -> None:
        errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(self._valid_summary())
        self.assertEqual(errors, [])

    def test_validate_summary_rejects_mismatch_reason_sum_drift(self) -> None:
        payload = self._valid_summary()
        payload["assess_snapshot_guard_mismatch_reason_counts"] = {"block_reason": 2}
        errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(payload)
        self.assertTrue(any("sum(assess_snapshot_guard_mismatch_reason_counts values)" in err for err in errors))

    def test_validate_summary_rejects_missing_required_numeric_field_without_crashing(self) -> None:
        payload = self._valid_summary()
        payload.pop("assess_rows_with_snapshot")
        errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(payload)
        self.assertTrue(any("assess_rows_with_snapshot must be non-negative integer" in err for err in errors))

    def test_validate_summary_rejects_guard_total_not_equal_with_snapshot(self) -> None:
        payload = self._valid_summary()
        payload["assess_rows_with_snapshot_guard_unverified"] = 1
        errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(payload)
        self.assertTrue(any("must equal assess_rows_with_snapshot" in err for err in errors))

    def test_validate_summary_rejects_missing_history_jsonl(self) -> None:
        payload = self._valid_summary()
        payload.pop("history_jsonl")
        errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(payload)
        self.assertTrue(any("history_jsonl must be non-empty string" in err for err in errors))

    def test_validate_summary_repo_path_scope_check(self) -> None:
        payload = self._valid_summary()
        ok_errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(
            payload,
            repo_root=REPO_ROOT,
            require_repo_paths=True,
        )
        self.assertEqual(ok_errors, [])

        payload["history_jsonl"] = "/var/folders/xx/outside_repo_history.jsonl"
        bad_errors = provider_onboarding_snapshot_guard_summary_validate.validate_summary(
            payload,
            repo_root=REPO_ROOT,
            require_repo_paths=True,
        )
        self.assertTrue(any("history_jsonl must resolve under repo root" in err for err in bad_errors))

    def test_main_fails_for_invalid_mismatch_key(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-summary-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            payload = self._valid_summary()
            payload["assess_snapshot_guard_mismatch_reason_counts"] = {"unexpected": 1}
            summary_json = tmp / "summary.json"
            summary_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            argv = [str(MODULE_PATH), "--summary-json", str(summary_json)]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_summary_validate.main()
            self.assertEqual(code, 2)

    def test_main_passes_for_valid_summary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-snapshot-guard-summary-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            payload = self._valid_summary()
            summary_json = tmp / "summary.json"
            summary_json.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            argv = [
                str(MODULE_PATH),
                "--summary-json",
                str(summary_json),
                "--repo-root",
                str(REPO_ROOT),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_snapshot_guard_summary_validate.main()
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
