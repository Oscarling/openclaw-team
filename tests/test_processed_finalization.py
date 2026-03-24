from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from skills import finalize_processed_previews as finalizer  # noqa: E402


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)

    def json(self) -> Any:
        return self._payload


class ProcessedFinalizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="argus-finalization-"))
        self.repo = self.tmpdir / "repo"
        self.repo.mkdir(parents=True, exist_ok=True)
        self._git(["init"], cwd=self.repo)
        self._git(["branch", "-M", "main"], cwd=self.repo)
        self._git(["config", "user.name", "Argus Test"], cwd=self.repo)
        self._git(["config", "user.email", "argus-test@example.com"], cwd=self.repo)
        (self.repo / ".gitignore").write_text(
            "\n".join(
                [
                    "artifacts/",
                    "tasks/",
                    "workspaces/",
                    "processed/*.json",
                    "processed/*.result.json",
                    "preview/*.json",
                    "preview/*.result.json",
                    "approvals/*.json",
                    "approvals/*.result.json",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (self.repo / "README.md").write_text("test repo\n", encoding="utf-8")
        self._git(["add", ".gitignore", "README.md"], cwd=self.repo)
        self._git(["commit", "-m", "initial"], cwd=self.repo)

        for relative in [
            "preview",
            "approvals",
            "processed",
            "tasks",
            "artifacts/scripts",
            "artifacts/reviews",
            "workspaces/automation",
            "workspaces/critic",
        ]:
            (self.repo / relative).mkdir(parents=True, exist_ok=True)

        self.preview_id = "preview-trello-card-1234567890ab-abcdef123456"
        self.card_id = "card-1234567890ab"
        self.board_id = "board-1234567890ab"
        self.todo_list_id = "list-todo-123"
        self.done_list_id = "list-done-456"
        self.preview_path = self.repo / "preview" / f"{self.preview_id}.json"
        self.approval_path = self.repo / "approvals" / f"{self.preview_id}.json"
        self.approval_result_path = self.repo / "approvals" / f"{self.preview_id}.json.result.json"
        self.processed_path = self.repo / "processed" / "trello-readonly-card-1234567890ab.json"
        self.processed_result_path = self.repo / "processed" / "trello-readonly-card-1234567890ab.json.result.json"
        self._old_env = {key: os.environ.get(key) for key in ("TRELLO_API_KEY", "TRELLO_API_TOKEN")}
        os.environ["TRELLO_API_KEY"] = "test-key"
        os.environ["TRELLO_API_TOKEN"] = "test-token"

    def tearDown(self) -> None:
        for key, value in self._old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def _git(self, args: list[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr or proc.stdout}")
        return proc

    def _write_execution_artifacts(self, *, auto_task_id: str, critic_task_id: str) -> None:
        (self.repo / "artifacts" / "scripts" / "pdf_to_excel_ocr_inbox_runner.py").write_text(
            "#!/usr/bin/env python3\nprint('hello')\n",
            encoding="utf-8",
        )
        (self.repo / "artifacts" / "reviews" / "pdf_to_excel_ocr_inbox_review.md").write_text(
            "# Review\n\nVerdict: pass\n",
            encoding="utf-8",
        )
        (self.repo / "tasks" / f"{auto_task_id}.json").write_text(
            json.dumps({"task_id": auto_task_id, "status": "success"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (self.repo / "tasks" / f"{critic_task_id}.json").write_text(
            json.dumps({"task_id": critic_task_id, "status": "success"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        auto_ws = self.repo / "workspaces" / "automation" / auto_task_id
        auto_ws.mkdir(parents=True, exist_ok=True)
        (auto_ws / "task.json").write_text(
            json.dumps({"task_id": auto_task_id, "worker": "automation"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (auto_ws / "output.json").write_text(
            json.dumps({"task_id": auto_task_id, "status": "success"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (auto_ws / "runtime.log").write_text("automation runtime\n", encoding="utf-8")

        critic_ws = self.repo / "workspaces" / "critic" / critic_task_id
        critic_ws.mkdir(parents=True, exist_ok=True)
        (critic_ws / "task.json").write_text(
            json.dumps({"task_id": critic_task_id, "worker": "critic"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (critic_ws / "output.json").write_text(
            json.dumps({"task_id": critic_task_id, "status": "success"}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (critic_ws / "runtime.log").write_text("critic runtime\n", encoding="utf-8")

    def _write_processed_preview(
        self,
        *,
        execution_status: str,
        decision_reason: str,
        auto_task_id: str = "AUTO-20260323-219",
        critic_task_id: str = "CRITIC-20260323-934",
    ) -> None:
        if execution_status == "processed":
            self._write_execution_artifacts(auto_task_id=auto_task_id, critic_task_id=critic_task_id)

        self.approval_path.write_text(
            json.dumps(
                {
                    "preview_id": self.preview_id,
                    "approved": True,
                    "approved_by": "test",
                    "approved_at": "2026-03-23T11:24:49Z",
                    "note": "test approval",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.approval_result_path.write_text(
            json.dumps(
                {
                    "preview_id": self.preview_id,
                    "status": execution_status,
                    "decision_reason": decision_reason,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.processed_path.write_text(
            json.dumps(
                {
                    "origin_id": f"trello:{self.card_id}",
                    "title": "manifest script",
                    "description": "desc",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self.processed_result_path.write_text(
            json.dumps(
                {
                    "preview_id": self.preview_id,
                    "status": "processed",
                    "decision": "preview_created_pending_approval",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        preview_payload = {
            "preview_id": self.preview_id,
            "approved": True,
            "source": {
                "kind": "local_inbox",
                "origin_id": f"trello:{self.card_id}",
                "received_at": "2026-03-23T11:24:28Z",
                "inbox_file": self.processed_path.name,
            },
            "external_input": {
                "title": "Generate one local PDF inventory manifest script (best-effort reviewable attempt)",
                "description": "short contract",
                "labels": ["trello", "reviewable"],
                "metadata": {
                    "card_id": self.card_id,
                    "board_id": self.board_id,
                    "list_id": self.todo_list_id,
                },
                "request_type": "pdf_to_excel_ocr",
                "input": {
                    "input_dir": "~/Desktop/pdf样本",
                    "output_xlsx": "artifacts/outputs/trello_readonly/pdf_to_excel_from_trello.xlsx",
                    "ocr": "auto",
                    "dry_run": False,
                },
            },
            "approval": {
                "approval_file": str(self.approval_path),
                "approved_by": "test",
                "approved_at": "2026-03-23T11:24:49Z",
                "note": "test approval",
            },
            "execution": {
                "status": execution_status,
                "executed": execution_status in {"processed", "rejected"},
                "attempts": 1,
                "executed_at": "2026-03-23T11:26:08Z",
                "decision_reason": decision_reason,
            },
            "last_execution": {
                "decision": execution_status,
                "decision_reason": decision_reason,
                "automation_result": {
                    "task_id": auto_task_id,
                    "worker": "automation",
                    "status": "success" if execution_status == "processed" else "failed",
                    "artifacts": [
                        {"path": "artifacts/scripts/pdf_to_excel_ocr_inbox_runner.py", "type": "script"}
                    ]
                    if execution_status == "processed"
                    else [],
                },
                "critic_result": {
                    "task_id": critic_task_id,
                    "worker": "critic",
                    "status": "success" if execution_status == "processed" else "failed",
                    "artifacts": [
                        {"path": "artifacts/reviews/pdf_to_excel_ocr_inbox_review.md", "type": "review"}
                    ]
                    if execution_status == "processed"
                    else [],
                    "metadata": {"verdict": "pass" if execution_status == "processed" else "fail"},
                },
                "critic_verdict": "pass" if execution_status == "processed" else "fail",
            },
        }
        self.preview_path.write_text(json.dumps(preview_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_finalize_processed_preview_commits_pushes_and_updates_trello(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")
        remote = self.tmpdir / "remote.git"
        self._git(["init", "--bare", str(remote)], cwd=self.tmpdir)

        def fake_get(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(
                200,
                [
                    {"id": self.todo_list_id, "name": "待办", "closed": False},
                    {"id": self.done_list_id, "name": "完成", "closed": False},
                ],
            )

        def fake_put(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(200, {"id": self.card_id, "idList": self.done_list_id})

        result = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=None,
            trello_done_list_name="完成",
            allow_replay_finalization=False,
            requests_get=fake_get,
            requests_put=fake_put,
        )

        self.assertEqual(result["status"], "completed")
        preview = json.loads(self.preview_path.read_text())
        self.assertEqual(preview["finalization"]["status"], "completed")
        commit_hash = preview["finalization"]["git"]["commit"]["commit_hash"]
        remote_head = self._git(["--git-dir", str(remote), "rev-parse", "refs/heads/main"], cwd=self.repo).stdout.strip()
        self.assertEqual(commit_hash, remote_head)
        self.assertEqual(preview["finalization"]["trello"]["status"], "success")

    def test_finalize_skips_non_processed_failure_branches(self) -> None:
        base_preview_id = self.preview_id
        cases = [
            ("critic_fail", "critic_verdict=fail"),
            ("worker_partial", "automation_status=partial"),
            ("runtime_error", "Automation task failed: runtime boom"),
        ]
        for suffix, reason in cases:
            with self.subTest(case=suffix):
                preview_path = self.repo / "preview" / f"{base_preview_id}-{suffix}.json"
                self.preview_path = preview_path
                self.approval_path = self.repo / "approvals" / f"{preview_path.stem}.json"
                self.approval_result_path = self.repo / "approvals" / f"{preview_path.stem}.json.result.json"
                self.processed_path = self.repo / "processed" / f"{preview_path.stem}.source.json"
                self.processed_result_path = self.repo / "processed" / f"{preview_path.stem}.source.json.result.json"
                self.preview_id = preview_path.stem
                self._write_processed_preview(execution_status="rejected", decision_reason=reason)
                result = finalizer.process_preview(
                    preview_path,
                    repo_root=self.repo,
                    git_remote=str(self.tmpdir / "unused.git"),
                    git_branch="main",
                    trello_done_list_id=self.done_list_id,
                    trello_done_list_name=None,
                    allow_replay_finalization=False,
                    requests_get=lambda *_a, **_k: FakeResponse(500, "should not be called"),
                    requests_put=lambda *_a, **_k: FakeResponse(500, "should not be called"),
                )
                self.assertEqual(result["status"], "skipped")
                self.assertIn("execution_status_not_processed:rejected", result["decision_reason"])

    def test_finalize_records_git_push_failure_and_retries(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")

        result = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(self.tmpdir / "missing-remote.git"),
            git_branch="main",
            trello_done_list_id=self.done_list_id,
            trello_done_list_name=None,
            allow_replay_finalization=False,
            requests_get=lambda *_a, **_k: FakeResponse(500, "should not be called"),
            requests_put=lambda *_a, **_k: FakeResponse(500, "should not be called"),
        )
        self.assertEqual(result["status"], "failed")
        failed_preview = json.loads(self.preview_path.read_text())
        first_commit_hash = failed_preview["finalization"]["git"]["commit"]["commit_hash"]
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["status"], "failed")

        remote = self.tmpdir / "retry-remote.git"
        self._git(["init", "--bare", str(remote)], cwd=self.tmpdir)

        def fake_put(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(200, {"id": self.card_id, "idList": self.done_list_id})

        retry = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=self.done_list_id,
            trello_done_list_name=None,
            allow_replay_finalization=False,
            requests_get=lambda *_a, **_k: FakeResponse(200, []),
            requests_put=fake_put,
        )
        self.assertEqual(retry["status"], "completed")
        retried_preview = json.loads(self.preview_path.read_text())
        self.assertEqual(first_commit_hash, retried_preview["finalization"]["git"]["commit"]["commit_hash"])

    def test_finalize_records_missing_git_remote_as_structured_failure(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")

        result = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=None,
            git_branch="main",
            trello_done_list_id=self.done_list_id,
            trello_done_list_name=None,
            allow_replay_finalization=False,
            requests_get=lambda *_a, **_k: FakeResponse(500, "should not be called"),
            requests_put=lambda *_a, **_k: FakeResponse(500, "should not be called"),
        )

        self.assertEqual(result["status"], "failed")
        self.assertIn("Missing git push remote", result["decision_reason"])
        failed_preview = json.loads(self.preview_path.read_text())
        self.assertEqual(failed_preview["finalization"]["status"], "failed")
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["status"], "failed")
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["reason"], "missing_git_push_remote")
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["remote"], "missing")

    def test_finalize_records_trello_failure_and_retries(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")
        remote = self.tmpdir / "remote-for-trello.git"
        self._git(["init", "--bare", str(remote)], cwd=self.tmpdir)

        def fake_get(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(200, [{"id": self.done_list_id, "name": "完成", "closed": False}])

        first = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=None,
            trello_done_list_name="完成",
            allow_replay_finalization=False,
            requests_get=fake_get,
            requests_put=lambda *_a, **_k: FakeResponse(500, "trello down"),
        )
        self.assertEqual(first["status"], "failed")
        failed_preview = json.loads(self.preview_path.read_text())
        commit_hash = failed_preview["finalization"]["git"]["commit"]["commit_hash"]
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["status"], "success")
        self.assertEqual(failed_preview["finalization"]["trello"]["status"], "failed")

        second = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=None,
            trello_done_list_name="完成",
            allow_replay_finalization=False,
            requests_get=fake_get,
            requests_put=lambda *_a, **_k: FakeResponse(200, {"id": self.card_id, "idList": self.done_list_id}),
        )
        self.assertEqual(second["status"], "completed")
        retried_preview = json.loads(self.preview_path.read_text())
        self.assertEqual(commit_hash, retried_preview["finalization"]["git"]["commit"]["commit_hash"])
        self.assertEqual(retried_preview["finalization"]["trello"]["status"], "success")

    def test_finalize_records_missing_trello_credentials_as_structured_failure(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")
        remote = self.tmpdir / "remote-missing-trello-creds.git"
        self._git(["init", "--bare", str(remote)], cwd=self.tmpdir)
        for name in ("TRELLO_API_KEY", "TRELLO_API_TOKEN", "TRELLO_KEY", "TRELLO_TOKEN"):
            os.environ.pop(name, None)

        result = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=self.done_list_id,
            trello_done_list_name=None,
            allow_replay_finalization=False,
            requests_get=lambda *_a, **_k: FakeResponse(500, "should not be called"),
            requests_put=lambda *_a, **_k: FakeResponse(500, "should not be called"),
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["decision_reason"], "Missing Trello write credentials")
        failed_preview = json.loads(self.preview_path.read_text())
        self.assertEqual(failed_preview["finalization"]["status"], "failed")
        self.assertEqual(failed_preview["finalization"]["git"]["push"]["status"], "success")
        self.assertEqual(failed_preview["finalization"]["trello"]["status"], "failed")
        self.assertEqual(
            failed_preview["finalization"]["trello"]["reason"],
            "missing_trello_write_credentials",
        )
        self.assertEqual(
            failed_preview["finalization"]["trello"]["presence"]["TRELLO_API_KEY"],
            "missing",
        )
        self.assertEqual(
            failed_preview["finalization"]["trello"]["presence"]["TRELLO_API_TOKEN"],
            "missing",
        )

    def test_finalize_completed_preview_is_replay_safe(self) -> None:
        self._write_processed_preview(execution_status="processed", decision_reason="critic_verdict=pass")
        remote = self.tmpdir / "remote-replay.git"
        self._git(["init", "--bare", str(remote)], cwd=self.tmpdir)

        def fake_get(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(200, [{"id": self.done_list_id, "name": "完成", "closed": False}])

        def fake_put(*_args: Any, **_kwargs: Any) -> FakeResponse:
            return FakeResponse(200, {"id": self.card_id, "idList": self.done_list_id})

        first = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=None,
            trello_done_list_name="完成",
            allow_replay_finalization=False,
            requests_get=fake_get,
            requests_put=fake_put,
        )
        self.assertEqual(first["status"], "completed")

        second = finalizer.process_preview(
            self.preview_path,
            repo_root=self.repo,
            git_remote=str(remote),
            git_branch="main",
            trello_done_list_id=None,
            trello_done_list_name="完成",
            allow_replay_finalization=False,
            requests_get=fake_get,
            requests_put=fake_put,
        )
        self.assertEqual(second["status"], "skipped")
        self.assertEqual(second["decision_reason"], "already_finalized_use_allow_replay_finalization")


if __name__ == "__main__":
    unittest.main()
