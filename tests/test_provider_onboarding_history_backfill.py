from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_backfill.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_backfill", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history backfill module from {MODULE_PATH}")
provider_onboarding_history_backfill = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_backfill)


class ProviderOnboardingHistoryBackfillTests(unittest.TestCase):
    def test_backfill_entries_uses_guard_and_backfills_matching_rows(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                        "note_class_counts": {"invalid_api_key": 4, "edge_policy_1010": 3, "tls_eof": 1},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            entries = [
                {
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"401": 4, "403": 4},
                    "assessment_json": str(assess),
                },
                {
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    "assessment_json": str(assess),
                },
            ]
            updated, stats = provider_onboarding_history_backfill.backfill_entries(entries)
            self.assertEqual(stats["backfilled"], 1)
            self.assertEqual(stats["skipped_guard_mismatch"], 1)
            self.assertNotIn("note_class_counts", updated[0])
            self.assertEqual(updated[1]["note_class_counts"]["tls_eof"], 1)

    def test_main_writes_backup_and_require_complete_can_fail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                        "note_class_counts": {"invalid_api_key": 4},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            history = tmp / "history.jsonl"
            rows = [
                {
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"401": 4, "403": 4},
                    "assessment_json": str(assess),
                },
                {
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    "assessment_json": str(assess),
                },
            ]
            history.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--require-complete",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_backfill.main()
            self.assertEqual(code, 2)
            self.assertTrue((Path(str(history) + ".bak")).exists())
            parsed = [
                json.loads(line)
                for line in history.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertNotIn("note_class_counts", parsed[0])
            self.assertEqual(parsed[1]["note_class_counts"]["invalid_api_key"], 4)

    def test_main_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                        "note_class_counts": {"invalid_api_key": 4},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            history = tmp / "history.jsonl"
            original_lines = [
                {
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    "assessment_json": str(assess),
                }
            ]
            history.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in original_lines) + "\n", encoding="utf-8")

            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--dry-run",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_backfill.main()
            self.assertEqual(code, 0)
            self.assertFalse((Path(str(history) + ".bak")).exists())
            parsed = [
                json.loads(line)
                for line in history.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertNotIn("note_class_counts", parsed[0])

    def test_backfill_prefers_assessment_snapshot_when_present(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            legacy_assess = tmp / "assessment_legacy.json"
            legacy_assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "http_code_counts": {"401": 4, "403": 4},
                        "note_class_counts": {"invalid_api_key": 4},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            snapshot_assess = tmp / "assessment_snapshot.json"
            snapshot_assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1, "401": 4, "403": 3},
                        "note_class_counts": {"invalid_api_key": 4, "tls_eof": 1},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            entries = [
                {
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    "assessment_json": str(legacy_assess),
                    "assessment_snapshot_json": str(snapshot_assess),
                }
            ]
            updated, stats = provider_onboarding_history_backfill.backfill_entries(entries)
            self.assertEqual(stats["backfilled"], 1)
            self.assertEqual(updated[0]["note_class_counts"]["tls_eof"], 1)


if __name__ == "__main__":
    unittest.main()
