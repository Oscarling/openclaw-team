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
        self.assertIn("Traceability:", condensed)
        self.assertIn("BL-20260324-014", condensed)
        self.assertNotIn("...", condensed)
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

        self.assertEqual(
            params["preferred_wrapper_script"],
            "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py",
        )
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
        self.assertIn("pdf_to_excel_ocr_inbox_runner.py", contract_hints["reuse_preference"])
        self.assertIn("artifacts/scripts/pdf_to_excel_ocr.py", contract_hints["reuse_preference"])
        self.assertIn("success/partial/failed", contract_hints["outcome_status_model"])
        self.assertIn("Path.cwd()", contract_hints["delegate_resolution"])
        self.assertIn("delegate only to the reviewed repository script", contract_hints["reviewed_delegate_contract"])
        self.assertIn("zero exit code plus output-file existence", contract_hints["delegate_success_evidence"])
        self.assertIn("status_counter.failed=0", contract_hints["delegate_success_evidence"])
        self.assertIn("status_counter.partial=0", contract_hints["delegate_success_evidence"])
        self.assertIn("excel_written=true", contract_hints["delegate_success_evidence"])
        self.assertIn("output_exists=true", contract_hints["delegate_success_evidence"])
        self.assertIn("output_size_bytes>0", contract_hints["delegate_success_evidence"])
        self.assertIn("wrapper status is success", contract_hints["delegate_success_evidence"])
        self.assertIn("status is partial", contract_hints["delegate_partial_evidence"])
        self.assertIn("status partial instead of escalating to failed", contract_hints["delegate_partial_evidence"])
        self.assertIn("next-step guidance", contract_hints["delegate_partial_evidence"])
        self.assertIn("explicit timeout", contract_hints["delegate_timeout"])
        self.assertIn(
            "status/total_files/status_counter/dry_run",
            contract_hints["delegate_report_schema"],
        )
        self.assertIn(
            "sidecar report file is available",
            contract_hints["delegate_report_handoff"],
        )
        self.assertIn(
            "--report-json",
            contract_hints["delegate_report_flag_contract"],
        )
        self.assertIn(
            "--report-file",
            contract_hints["delegate_report_flag_contract"],
        )
        self.assertIn(
            "do not short-circuit dry-run",
            contract_hints["dry_run_semantics"],
        )
        self.assertIn(
            "recursive vs non-recursive",
            contract_hints["pdf_discovery_consistency"],
        )
        self.assertTrue(
            any(
                "Preserve meaningful traceability from the incoming description" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "report a reviewable partial outcome" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "pdf_to_excel_ocr_inbox_runner.py already exists" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "status/total_files/status_counter/dry_run" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "excel_written=true" in item and "status_counter.partial=0" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "keep wrapper status partial (not failed)" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "sidecar report is present" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "--report-json exactly" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "do not short-circuit dry-run" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertTrue(
            any(
                "PDF discovery semantics aligned" in item
                for item in auto_task["constraints"]
            )
        )
        self.assertIn(
            "If output_xlsx ends with .xlsx, the artifact must preserve true XLSX output semantics or fail honestly before writing a mismatched format.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Dry-run or zero-input behavior is represented as a reviewable partial outcome instead of artifact-production success.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Wrapper success requires stronger delegate evidence than zero exit code plus a non-empty output file alone.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Wrapper success attestation requires delegate fields excel_written=true, output_exists=true, output_size_bytes>0, and status_counter.partial/status_counter.failed equal to 0.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Contract-compliant delegate partial outcomes remain partial with explicit limitations and next-step guidance, rather than being escalated to failed by success-only gates.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Wrapper evidence logic remains compatible with delegate JSON fields status/total_files/status_counter/dry_run.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Delegate report handoff prefers sidecar JSON as canonical evidence and only falls back to stdout JSON when sidecar evidence is unavailable.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Wrapper/delegate sidecar report handoff remains CLI-compatible by using --report-json (or another explicitly supported delegate alias).",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Dry-run semantics remain explicit and delegated for readonly governed flows: pass --dry-run through delegate and preserve partial outcome honestly.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Wrapper preflight PDF discovery semantics remain aligned with delegate discovery semantics to keep evidence counts consistent.",
            auto_task["acceptance_criteria"],
        )
        self.assertIn(
            "Delegate execution is bounded by an explicit timeout and reports timeout honestly.",
            auto_task["acceptance_criteria"],
        )
        self.assertEqual(
            auto_task["metadata"]["automation_contract_profile"],
            "narrow_script_artifact_with_repo_reuse_and_reviewable_runner_contract",
        )
        self.assertEqual(
            task.critic_task["inputs"]["artifacts"],
            [
                {"path": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py", "type": "script"},
                {"path": "artifacts/scripts/pdf_to_excel_ocr.py", "type": "script"},
            ],
        )
        self.assertIn("reviewed delegate script", task.critic_task["objective"])
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
