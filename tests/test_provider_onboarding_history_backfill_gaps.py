from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "provider_onboarding_history_backfill_gaps.py"
SPEC = importlib.util.spec_from_file_location("provider_onboarding_history_backfill_gaps", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load provider onboarding history backfill gaps module from {MODULE_PATH}")
provider_onboarding_history_backfill_gaps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(provider_onboarding_history_backfill_gaps)


class ProviderOnboardingHistoryBackfillGapsTests(unittest.TestCase):
    def test_build_gap_report_classifies_mismatch_and_backfillable(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-gaps-") as tmp_raw:
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
            history_rows = [
                {
                    "timestamp": "2026-03-28T12:07:46",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "auth_or_access_policy_block",
                    "http_code_counts": {"401": 4, "403": 4},
                    "assessment_json": str(assess),
                },
                {
                    "timestamp": "2026-03-28T12:26:50",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1, "401": 4, "403": 3},
                    "assessment_json": str(assess),
                },
            ]
            report = provider_onboarding_history_backfill_gaps.build_gap_report(history_rows, Path("history.jsonl"))
            self.assertEqual(report["missing_note_count_rows"], 2)
            self.assertEqual(report["reason_counts"]["guard_mismatch_block_reason"], 1)
            self.assertEqual(report["reason_counts"]["backfillable_now"], 1)
            self.assertEqual(report["missing_rows"][0]["detail"]["source_field"], "assessment_json")

    def test_main_writes_report_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-gaps-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1},
                        "note_class_counts": {"tls_eof": 1},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            history = tmp / "history.jsonl"
            history.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-03-28T12:26:50",
                        "stamp": "20260328",
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1},
                        "assessment_json": str(assess),
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            out = tmp / "gaps.json"
            argv = [
                str(MODULE_PATH),
                "--history-jsonl",
                str(history),
                "--output-json",
                str(out),
            ]
            with mock.patch.object(sys, "argv", argv):
                code = provider_onboarding_history_backfill_gaps.main()
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["missing_note_count_rows"], 1)
            self.assertEqual(payload["reason_counts"]["backfillable_now"], 1)

    def test_gap_report_prefers_snapshot_source_field(self) -> None:
        with tempfile.TemporaryDirectory(prefix="provider-onboarding-history-gaps-") as tmp_raw:
            tmp = Path(tmp_raw)
            assess = tmp / "assessment_snapshot.json"
            assess.write_text(
                json.dumps(
                    {
                        "status": "blocked",
                        "block_reason": "mixed_with_tls_transport_failures",
                        "http_code_counts": {"000": 1},
                        "note_class_counts": {"tls_eof": 1},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            history_rows = [
                {
                    "timestamp": "2026-03-28T12:26:50",
                    "stamp": "20260328",
                    "status": "blocked",
                    "block_reason": "mixed_with_tls_transport_failures",
                    "http_code_counts": {"000": 1},
                    "assessment_json": str(tmp / "assessment_legacy.json"),
                    "assessment_snapshot_json": str(assess),
                }
            ]
            report = provider_onboarding_history_backfill_gaps.build_gap_report(history_rows, Path("history.jsonl"))
            self.assertEqual(report["reason_counts"]["backfillable_now"], 1)
            self.assertEqual(report["missing_rows"][0]["detail"]["source_field"], "assessment_snapshot_json")


if __name__ == "__main__":
    unittest.main()
