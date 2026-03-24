from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from adapters import local_inbox_adapter
from argus_contracts import validate_task


class LocalInboxAdapterTests(unittest.TestCase):
    def _sample_payload(self, *, origin_id: str | None, regeneration_token: str | None = None) -> dict:
        payload = {
            "title": "Fresh Trello preview execution follow-up",
            "description": (
                "Purpose:\n\n"
                "Controlled Trello live preview smoke for openclaw-team.\n\n"
                "Expected behavior:\n"
                "- read-only Trello ingest\n"
                "- preview creation smoke only\n\n"
                "Traceability:\n"
                "- backlog: BL-20260324-020\n\n"
                "Execution contract: treat this as a best-effort, evidence-backed PDF extraction/conversion attempt."
            ),
            "labels": ["trello", "readonly", "reviewable"],
            "request_type": "pdf_to_excel_ocr",
            "input": {
                "input_dir": "/tmp/pdf-samples",
                "output_xlsx": "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx",
                "ocr": "auto",
                "dry_run": False,
            },
            "metadata": {"source_system": "trello"},
        }
        if origin_id is not None:
            payload["origin_id"] = origin_id
        if regeneration_token is not None:
            payload["regeneration_token"] = regeneration_token
        return payload

    def test_condense_automation_description_preserves_meaningful_context(self) -> None:
        description = """
Purpose:

  Controlled Trello live preview smoke for openclaw-team.

Expected behavior:
- read-only Trello ingest
- preview creation smoke only

Traceability:
- backlog: BL-20260324-014

Execution contract: treat this as a best-effort, evidence-backed PDF extraction/conversion attempt.
""".strip()

        condensed = local_inbox_adapter._condense_automation_description(description)

        self.assertNotEqual(condensed, "Purpose:")
        self.assertIn("Controlled Trello live preview smoke", condensed)
        self.assertIn("Expected behavior:", condensed)
        self.assertNotIn("Execution contract:", condensed)

    def test_normalize_local_inbox_payload_adds_contract_hints_for_pdf_to_excel(self) -> None:
        raw_payload = self._sample_payload(origin_id="trello:test-card-123")

        with tempfile.TemporaryDirectory(prefix="local-inbox-adapter-") as tmp:
            base_dir = Path(tmp)
            task = local_inbox_adapter.normalize_local_inbox_payload(
                raw_payload,
                inbox_filename="trello-readonly-test-card.json",
                base_dir=base_dir,
            )

        auto_task = task.automation_task
        params = auto_task["inputs"]["params"]
        contract_hints = params["contract_hints"]

        self.assertEqual(params["preferred_base_script"], "artifacts/scripts/pdf_to_excel_ocr.py")
        self.assertEqual(
            params["reference_docs"],
            [
                "artifacts/docs/pdf_to_excel_ocr_usage.md",
                "artifacts/reviews/pdf_to_excel_ocr_review.md",
            ],
        )
        self.assertIn("Controlled Trello live preview smoke", params["description"])
        self.assertIn("Expected behavior:", params["description"])
        self.assertIn("real XLSX workbook container", contract_hints["output_format_fidelity"])
        self.assertIn("Do not hardcode", contract_hints["path_portability"])
        self.assertIn("artifacts/scripts/pdf_to_excel_ocr.py", contract_hints["reuse_preference"])
        self.assertTrue(
            any(
                "Preserve meaningful traceability from the incoming description" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertIn(
            "If output_xlsx ends with .xlsx, the artifact must preserve true XLSX output semantics or fail honestly before writing a mismatched format.",
            auto_task["acceptance_criteria"],
        )
        self.assertEqual(
            auto_task["metadata"]["automation_contract_profile"],
            "narrow_script_artifact_with_repo_reuse_and_format_fidelity",
        )
        self.assertEqual(validate_task(auto_task), [])

    def test_normalize_local_inbox_payload_uses_explicit_regeneration_token_for_dedupe(self) -> None:
        raw_payload = self._sample_payload(
            origin_id="trello:test-card-123",
            regeneration_token="regen-20260324-a",
        )

        with tempfile.TemporaryDirectory(prefix="local-inbox-adapter-") as tmp:
            base_dir = Path(tmp)
            task = local_inbox_adapter.normalize_local_inbox_payload(
                raw_payload,
                inbox_filename="trello-readonly-test-card.json",
                base_dir=base_dir,
            )

        self.assertEqual(task.regeneration_token, "regen-20260324-a")
        self.assertEqual(
            task.dedupe_keys[0],
            "origin_regeneration:trello:test-card-123:regen-20260324-a",
        )
        self.assertNotIn("origin:trello:test-card-123", task.dedupe_keys)
        self.assertEqual(task.source["regeneration_token"], "regen-20260324-a")
        self.assertEqual(task.metadata["regeneration_token"], "regen-20260324-a")
        self.assertEqual(
            task.automation_task["metadata"]["regeneration_token"],
            "regen-20260324-a",
        )
        self.assertEqual(
            task.critic_task["metadata"]["regeneration_token"],
            "regen-20260324-a",
        )

    def test_validate_external_payload_rejects_regeneration_without_explicit_origin(self) -> None:
        raw_payload = self._sample_payload(origin_id=None, regeneration_token="regen-20260324-a")

        with self.assertRaisesRegex(RuntimeError, "regeneration_token requires an explicit origin_id"):
            local_inbox_adapter.validate_external_payload(
                raw_payload,
                inbox_filename="trello-readonly-test-card.json",
            )


if __name__ == "__main__":
    unittest.main()
