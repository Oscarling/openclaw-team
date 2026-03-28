from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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

    def test_build_critic_from_automation_keeps_full_content_under_default_limit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            runner_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr_inbox_runner.py"
            delegate_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr.py"
            runner_path.parent.mkdir(parents=True, exist_ok=True)
            # Size chosen above legacy 12k truncation threshold and below new default limit.
            large_runner = ("x" * 15050) + "\n"
            runner_path.write_text(large_runner, encoding="utf-8")
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

            runner_snapshot = updated["inputs"]["params"]["artifact_snapshots"][0]
            self.assertFalse(runner_snapshot["truncated"])
            self.assertEqual(runner_snapshot["content"], large_runner)

    def test_build_critic_from_automation_truncates_when_limit_exceeded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            runner_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr_inbox_runner.py"
            delegate_path = repo_root / "artifacts" / "scripts" / "pdf_to_excel_ocr.py"
            runner_path.parent.mkdir(parents=True, exist_ok=True)
            runner_path.write_text("abcdefghijklmnopqrstuvwxyz", encoding="utf-8")
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
                with mock.patch.object(executor, "MAX_SNAPSHOT_CHARS", 8):
                    updated = executor.build_critic_from_automation(critic_task, auto_result)
            finally:
                executor.REPO_ROOT = original_repo_root

            runner_snapshot = updated["inputs"]["params"]["artifact_snapshots"][0]
            self.assertTrue(runner_snapshot["truncated"])
            self.assertEqual(runner_snapshot["content"], "abcdefgh")


class ExecuteApprovedPreviewsTransientRetryTests(unittest.TestCase):
    def _valid_automation_task(self) -> dict:
        return {
            "task_id": "AUTO-20260326-901",
            "worker": "automation",
            "task_type": "generate_script",
            "objective": "Generate a deterministic automation artifact for retry validation.",
            "inputs": {"params": {"script_name": "demo.py"}},
            "expected_outputs": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
            "constraints": ["must be deterministic"],
        }

    def _valid_critic_task(self) -> dict:
        return {
            "task_id": "CRITIC-20260326-901",
            "worker": "critic",
            "task_type": "review_artifact",
            "objective": "Review generated automation artifact and return deterministic verdict.",
            "inputs": {"artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}]},
            "expected_outputs": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
            "constraints": ["must include verdict"],
        }

    def test_process_approval_retries_once_for_http_524_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": [
                            "LLM call exhausted (attempts=4/4, class=http_524, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True): HTTP Error 524: <none>"
                        ],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_timeout_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-timeout"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": [
                            "LLM call exhausted (attempts=1/1, class=timeout, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True): The read operation timed out"
                        ],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_http_502_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-http502"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": [
                            "LLM call exhausted (attempts=1/1, class=http_502, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True): HTTP Error 502: Bad Gateway"
                        ],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_http_520_without_class_tag_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-http520"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": ["HTTP Error 520: Web Server Returned an Unknown Error"],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_tls_eof_without_class_tag_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-tlseof"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": [
                            "<urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol>"
                        ],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_dns_resolution_without_class_tag_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-dns"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": "Worker execution failed",
                        "artifacts": [],
                        "errors": [
                            "<urlopen error [Errno 8] nodename nor servname provided, or not known>"
                        ],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_retries_once_for_workspace_presence_failure_then_succeeds(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-001-workspace"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation" and calls.count("automation") == 1:
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "failed",
                        "summary": (
                            "Unable to generate the requested helper script because the execution "
                            "environment did not provide repository access (no /app/workspaces/automation "
                            "path or task.json was available)."
                        ),
                        "artifacts": [],
                        "errors": ["Worker reported failed without structured errors"],
                        "metadata": {},
                    }
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.dict(
                    "os.environ",
                    {
                        "ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS": "0",
                        "ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS": "1",
                    },
                    clear=False,
                ):
                    with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                        result = executor.process_approval(
                            approval_path,
                            approval_payload,
                            SimpleNamespace(test_mode="off", allow_replay=True),
                        )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(result["automation_transient_retries_used"], 0)
            self.assertEqual(result["automation_workspace_retries_used"], 1)
            self.assertEqual(calls, ["automation", "automation", "critic"])

    def test_process_approval_does_not_retry_non_transient_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)

            preview_id = "preview-test-002"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "pending"},
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                return {
                    "task_id": task["task_id"],
                    "worker": worker,
                    "status": "failed",
                    "summary": "Worker execution failed",
                    "artifacts": [],
                    "errors": [
                        "LLM call exhausted (attempts=1/1, class=http_403, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=False): HTTP Error 403: Forbidden"
                    ],
                    "metadata": {},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=True),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "rejected")
            self.assertEqual(result["automation_transient_retries_used"], 0)
            self.assertEqual(calls, ["automation"])

    def test_process_approval_allows_one_auto_replay_for_retryable_rejected_preview(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            artifacts_dir = repo_root / "artifacts"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "reviews").mkdir(parents=True, exist_ok=True)
            (artifacts_dir / "scripts" / "demo.py").write_text("print('ok')\n", encoding="utf-8")
            (artifacts_dir / "reviews" / "demo_review.md").write_text(
                "# Review\n\n- Verdict: pass\n", encoding="utf-8"
            )

            preview_id = "preview-test-003-auto-replay"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "rejected", "attempts": 1},
                "last_execution": {
                    "decision": "rejected",
                    "decision_reason": "Automation task failed",
                    "automation_result": {
                        "status": "failed",
                        "errors": [
                            "LLM call exhausted (attempts=1/1, class=http_520, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True): HTTP Error 520: Bad Gateway"
                        ],
                    },
                },
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            calls: list[str] = []

            def fake_delegate(worker: str, task: dict, **kwargs: object) -> dict:  # noqa: ARG001
                calls.append(worker)
                if worker == "automation":
                    return {
                        "task_id": task["task_id"],
                        "worker": "automation",
                        "status": "success",
                        "summary": "automation success",
                        "artifacts": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
                        "metadata": {},
                    }
                return {
                    "task_id": task["task_id"],
                    "worker": "critic",
                    "status": "success",
                    "summary": "critic success",
                    "artifacts": [{"path": "artifacts/reviews/demo_review.md", "type": "review"}],
                    "metadata": {"verdict": "pass"},
                }

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                with mock.patch.object(executor, "delegate_task", side_effect=fake_delegate):
                    result = executor.process_approval(
                        approval_path,
                        approval_payload,
                        SimpleNamespace(test_mode="off", allow_replay=False),
                    )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["critic_verdict"], "pass")
            self.assertEqual(calls, ["automation", "critic"])

    def test_process_approval_skips_retryable_rejected_preview_after_auto_replay_budget_exhausted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="execute-approved-previews-") as tmp:
            repo_root = Path(tmp)
            preview_dir = repo_root / "preview"
            approvals_dir = repo_root / "approvals"
            preview_dir.mkdir(parents=True, exist_ok=True)
            approvals_dir.mkdir(parents=True, exist_ok=True)

            preview_id = "preview-test-004-auto-replay-budget"
            preview_payload = {
                "preview_id": preview_id,
                "internal_tasks": {
                    "automation": self._valid_automation_task(),
                    "critic": self._valid_critic_task(),
                },
                "execution": {"status": "rejected", "attempts": 2},
                "last_execution": {
                    "decision": "rejected",
                    "decision_reason": "Automation task failed",
                    "automation_result": {
                        "status": "failed",
                        "errors": [
                            "LLM call exhausted (attempts=1/1, class=http_520, endpoint=https://fast.vpsairobot.com/v1/chat/completions, retryable=True): HTTP Error 520: Bad Gateway"
                        ],
                    },
                },
            }
            approval_payload = {
                "preview_id": preview_id,
                "approved": True,
                "approved_by": "tester",
                "approved_at": "2026-03-26T00:00:00Z",
            }
            preview_path = preview_dir / f"{preview_id}.json"
            approval_path = approvals_dir / f"{preview_id}.json"
            preview_path.write_text(json.dumps(preview_payload), encoding="utf-8")
            approval_path.write_text(json.dumps(approval_payload), encoding="utf-8")

            original_repo_root = executor.REPO_ROOT
            original_preview_dir = executor.PREVIEW_DIR
            original_approvals_dir = executor.APPROVALS_DIR
            try:
                executor.REPO_ROOT = repo_root
                executor.PREVIEW_DIR = preview_dir
                executor.APPROVALS_DIR = approvals_dir
                result = executor.process_approval(
                    approval_path,
                    approval_payload,
                    SimpleNamespace(test_mode="off", allow_replay=False),
                )
            finally:
                executor.REPO_ROOT = original_repo_root
                executor.PREVIEW_DIR = original_preview_dir
                executor.APPROVALS_DIR = original_approvals_dir

            self.assertEqual(result["status"], "skipped")
            self.assertEqual(result["decision_reason"], "already_executed_use_allow_replay")


if __name__ == "__main__":
    unittest.main()
