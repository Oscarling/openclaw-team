from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_snapshot_backfill.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_snapshot_backfill", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history snapshot backfill module from {MODULE_PATH}")
provider_onboarding_history_snapshot_backfill = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_snapshot_backfill)


class ProviderOnboardingHistorySnapshotBackfillTests(unittest.TestCase):
    def test_backfill_snapshot_entries_skips_non_assess_and_backfills_assess(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-snapshot-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                        "http_code_counts": {"401": 1, "403": 1},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            entries = [
                {
                    "timestamp": "2026-03-28T13:01:02",
                    "stamp": "20260328",
                    "phase": "assess",
                    "assessment_json": str(assess),
                },
                {
                    "timestamp": "2026-03-28T13:01:03",
                    "stamp": "20260328",
                    "phase": "probe",
                    "assessment_json": str(assess),
                },
            ]
            snapshot_dir = tmp / "snapshots"
            updated, stats = provider_onboarding_history_snapshot_backfill.backfill_snapshot_entries(
                entries,
                snapshot_dir=snapshot_dir,
                dry_run=True,
            )

            self.assertEqual(stats["backfilled"], 1)
            self.assertEqual(stats["skipped_non_assess"], 1)
            self.assertIn("assessment_snapshot_json", updated[0])
            self.assertIn("line1", updated[0]["assessment_snapshot_json"])
            self.assertNotIn("assessment_snapshot_json", updated[1])
            self.assertFalse(snapshot_dir.exists())

    def test_main_writes_backup_and_snapshot_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-snapshot-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess_payload = {
                "status": "blocked",
                "block_reason": "mixed_with_tls_transport_failures",
                "http_code_counts": {"000": 1, "401": 4, "403": 3},
                "note_class_counts": {"invalid_api_key": 4, "tls_eof": 1},
            }
            assess.write_text(json.dumps(assess_payload, ensure_ascii=False) + "\n", encoding="utf-8")
            history = tmp / "history.jsonl"
            history.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T13:05:06",
                        "stamp": "20260328",
                        "phase": "assess",
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "assessment_json": str(assess),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            snapshot_dir = tmp / "snapshots"
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--snapshot-dir",
                str(snapshot_dir),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_snapshot_backfill.main()

            self.assertEqual(code, 0)
            self.assertTrue((Path(str(history) + ".bak")).exists())
            parsed = [json.loads(line) for line in history.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual(len(parsed), 1)
            snapshot_path = Path(parsed[0]["assessment_snapshot_json"])
            self.assertTrue(snapshot_path.exists())
            snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
            self.assertEqual(snapshot_payload["note_class_counts"]["tls_eof"], 1)

    def test_backfill_snapshot_entries_repairs_missing_snapshot_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-snapshot-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            entries = [
                {
                    "timestamp": "2026-03-28T13:01:02",
                    "stamp": "20260328",
                    "phase": "assess",
                    "assessment_json": str(assess),
                    "assessment_snapshot_json": str(tmp / "missing_snapshot.json"),
                }
            ]
            snapshot_dir = tmp / "snapshots"
            updated, stats = provider_onboarding_history_snapshot_backfill.backfill_snapshot_entries(
                entries,
                snapshot_dir=snapshot_dir,
                dry_run=False,
            )
            self.assertEqual(stats["backfilled"], 1)
            self.assertTrue(Path(updated[0]["assessment_snapshot_json"]).exists())

    def test_backfill_snapshot_entries_normalizes_existing_relative_snapshot_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-snapshot-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps({"status": "blocked", "block_reason": "auth_or_access_policy_block"}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            relative_snapshot = Path("snapshots") / "relative_snapshot.json"
            absolute_snapshot = tmp / relative_snapshot
            absolute_snapshot.parent.mkdir(parents=True, exist_ok=True)
            absolute_snapshot.write_text("{}", encoding="utf-8")

            entries = [
                {
                    "timestamp": "2026-03-28T13:01:02",
                    "stamp": "20260328",
                    "phase": "assess",
                    "assessment_json": str(assess),
                    "assessment_snapshot_json": str(relative_snapshot),
                }
            ]
            with mock.patch.object(provider_onboarding_history_snapshot_backfill, "REPO_ROOT", tmp):
                updated, stats = provider_onboarding_history_snapshot_backfill.backfill_snapshot_entries(
                    entries,
                    snapshot_dir=tmp / "snapshots-out",
                    dry_run=True,
                )
            self.assertEqual(stats["already_present"], 1)
            self.assertEqual(stats["normalized_existing"], 1)
            self.assertEqual(updated[0]["assessment_snapshot_json"], str(absolute_snapshot.resolve()))

    def test_main_require_complete_fails_when_missing_assessment_path_remains(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-snapshot-backfill-") as tmp_raw:
            tmp = Path(tmp_raw)
            history = tmp / "history.jsonl"
            history.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T13:05:06",
                        "stamp": "20260328",
                        "phase": "assess",
                        "status": "blocked",
                        "block_reason": "auth_or_access_policy_block",
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
                "--require-complete",
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_snapshot_backfill.main()
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
