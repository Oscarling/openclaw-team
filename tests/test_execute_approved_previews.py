from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills import execute_approved_previews as executor


class CriticVerdictExtractionTests(unittest.TestCase):
    def test_prefers_final_explicit_verdict_line_over_embedded_contract_text(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            review_path = repo_root / "artifacts" / "reviews" / "sample_review.md"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                "\n".join(
                    [
                        "# Review",
                        "",
                        "- Reviewed artifact target: {'fallback_policy': 'If evidence is insufficient, set verdict=needs_revision.'}",
                        "- Verdict: pass (test mode)",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            original_repo_root = executor.REPO_ROOT
            try:
                executor.REPO_ROOT = repo_root
                verdict = executor.extract_critic_verdict(
                    {
                        "status": "success",
                        "summary": "Forced success output for CRITIC in test mode.",
                        "artifacts": [{"path": "artifacts/reviews/sample_review.md", "type": "review"}],
                        "metadata": {"test_mode": True, "scenario": "success"},
                    },
                    "artifacts/reviews/sample_review.md",
                )
            finally:
                executor.REPO_ROOT = original_repo_root

            self.assertEqual(verdict, "pass")

    def test_reads_verdict_from_heading_section(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            review_path = repo_root / "artifacts" / "reviews" / "section_review.md"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                "\n".join(
                    [
                        "# Review",
                        "",
                        "## Findings",
                        "- Looks acceptable.",
                        "",
                        "## Verdict",
                        "needs_revision",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            original_repo_root = executor.REPO_ROOT
            try:
                executor.REPO_ROOT = repo_root
                verdict = executor.extract_critic_verdict(
                    {"status": "partial", "summary": "Review generated.", "metadata": {}},
                    "artifacts/reviews/section_review.md",
                )
            finally:
                executor.REPO_ROOT = original_repo_root

            self.assertEqual(verdict, "needs_revision")

    def test_build_critic_from_automation_preserves_declared_delegate_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            runner_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr_inbox_runner.py"
            delegate_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr.py"
            runner_path.parent.mkdir(parents=True, exist_ok=True)
            runner_path.write_text("print('runner')\n", encoding="utf-8")
            delegate_path.write_text("print('delegate')\n", encoding="utf-8")

            critic_task = {
                "inputs": {
                    "artifacts": [
                        {"path": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py", "type": "script"},
                        {"path": "artifacts/scripts/pdf_to_excel_ocr.py", "type": "script"},
                    ],
                    "params": {"review_scope": "pair"},
                },
                "expected_outputs": [
                    {"path": "artifacts/reviews/pdf_to_excel_ocr_inbox_review.md", "type": "review"}
                ],
                "constraints": [],
            }
            auto_result = {
                "artifacts": [
                    {"path": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py", "type": "script"}
                ]
            }

            original_repo_root = executor.REPO_ROOT
            try:
                executor.REPO_ROOT = repo_root
                updated = executor.build_critic_from_automation(critic_task, auto_result)
            finally:
                executor.REPO_ROOT = original_repo_root

            self.assertEqual(
                updated["inputs"]["artifacts"],
                [
                    {"path": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py", "type": "script"},
                    {"path": "artifacts/scripts/pdf_to_excel_ocr.py", "type": "script"},
                ],
            )
            snapshots = updated["inputs"]["params"]["artifact_snapshots"]
            self.assertEqual(
                [item["path"] for item in snapshots],
                [
                    "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py",
                    "artifacts/scripts/pdf_to_excel_ocr.py",
                ],
            )
            self.assertIn("runner", snapshots[0]["content"])
            self.assertIn("delegate", snapshots[1]["content"])


if __name__ == "__main__":
    unittest.main()
