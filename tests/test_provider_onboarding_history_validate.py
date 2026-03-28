from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_validate.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_validate", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history validate module from {MODULE_PATH}")
provider_onboarding_history_validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_validate)


class ProviderOnboardingHistoryValidateTests(unittest.TestCase):
    def test_validate_entry_accepts_well_formed_assess_row(self) -> None:
        row = {
            "timestamp": "2026-03-28T12:26:50",
            "stamp": "20260328",
            "phase": "assess",
            "status": "blocked",
            "block_reason": "mixed_with_tls_transport_failures",
            "exit_code": 2,
            "probe_tsv": "/tmp/probe.tsv",
            "assessment_json": "/tmp/assessment.json",
            "success_row_count": 0,
            "http_code_counts": {"000": 1, "401": 4, "403": 3},
        }
        errors = provider_onboarding_history_validate.validate_entry(
            row,
            line_no=1,
            repo_root=Path("/Users/demo/repo"),
            require_repo_paths=False,
        )
        self.assertEqual(errors, [])

    def test_validate_entry_rejects_non_repo_paths_when_required(self) -> None:
        row = {
            "timestamp": "2026-03-28T12:26:50",
            "stamp": "20260328",
            "phase": "assess",
            "status": "blocked",
            "block_reason": "auth_or_access_policy_block",
            "exit_code": 2,
            "probe_tsv": "/var/folders/nonrepo_probe.tsv",
            "assessment_json": "/var/folders/nonrepo_assessment.json",
        }
        errors = provider_onboarding_history_validate.validate_entry(
            row,
            line_no=3,
            repo_root=Path("/Users/demo/repo"),
            require_repo_paths=True,
        )
        self.assertTrue(any("probe_tsv must be absolute repo path" in err for err in errors))
        self.assertTrue(any("assessment_json must be absolute repo path" in err for err in errors))

    def test_validate_history_reports_invalid_json_and_schema_errors(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            history.write_text(
                "{bad-json}\n"
                + json.dumps(
                    {
                        "timestamp": "2026-03-28T12:26:50",
                        "stamp": "bad",
                        "phase": "assess",
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "exit_code": -1,
                        "probe_tsv": str(tmp / "probe.tsv"),
                        "assessment_json": str(tmp / "assessment.json"),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            errors = provider_onboarding_history_validate.validate_history(
                history_path=history,
                repo_root=tmp,
                require_repo_paths=False,
            )
            self.assertTrue(any("line 1: invalid JSON" in err for err in errors))
            self.assertTrue(any("line 2: stamp must be YYYYMMDD string" in err for err in errors))
            self.assertTrue(any("line 2: exit_code must be non-negative integer" in err for err in errors))

    def test_validate_entry_rejects_invalid_note_class_counts_shape(self) -> None:
        row = {
            "timestamp": "2026-03-28T12:26:50",
            "stamp": "20260328",
            "phase": "assess",
            "status": "blocked",
            "block_reason": "mixed_with_tls_transport_failures",
            "exit_code": 2,
            "probe_tsv": "/tmp/probe.tsv",
            "assessment_json": "/tmp/assessment.json",
            "note_class_counts": {"": 1, "tls_eof": -1},
        }
        errors = provider_onboarding_history_validate.validate_entry(
            row,
            line_no=5,
            repo_root=Path("/Users/demo/repo"),
            require_repo_paths=False,
        )
        self.assertTrue(any("note_class_counts key must be non-empty string" in err for err in errors))
        self.assertTrue(any("note_class_counts value must be non-negative integer" in err for err in errors))

    def test_main_passes_for_repo_scoped_history(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-validate-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            history.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T12:26:50",
                        "stamp": "20260328",
                        "phase": "assess",
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "exit_code": 2,
                        "probe_tsv": str(tmp / "probe.tsv"),
                        "assessment_json": str(tmp / "assessment.json"),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--repo-root",
                str(tmp),
                "--require-repo-paths",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_validate.main()
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
