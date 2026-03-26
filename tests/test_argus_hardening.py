from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from argus_contracts import validate_output  # noqa: E402
from dispatcher import worker_runtime  # noqa: E402
from skills.delegate_task import build_worker_env, delegate_task  # noqa: E402

WORKER_TASK_TYPES = {
    "architect": "design_architecture",
    "devops": "setup_infrastructure",
    "automation": "generate_script",
    "critic": "review_artifact",
}


class FakeImages:
    def __init__(self) -> None:
        self.available: set[str] = set()
        self.build_calls: list[dict[str, Any]] = []

    def get(self, tag: str) -> dict[str, str]:
        if tag not in self.available:
            raise RuntimeError(f"image not found: {tag}")
        return {"tag": tag}

    def build(self, **kwargs: Any) -> tuple[dict[str, str], list[str]]:
        tag = kwargs["tag"]
        self.available.add(tag)
        self.build_calls.append(kwargs)
        return {"tag": tag}, ["built"]


class FakeContainer:
    def __init__(self, *, client: "FakeDockerClient", image: str, command: list[str], name: str, environment: dict[str, str]) -> None:
        self.client = client
        self.image = image
        self.command = command
        self.name = name
        self.environment = environment
        self._stdout = ""
        self._stderr = ""
        self._ran = False
        self.removed = False
        task_dir_arg = command[command.index("--task-dir") + 1]
        self.task_dir = (client.base_dir / Path(task_dir_arg).relative_to("/app")).resolve()
        self.worker = command[command.index("--worker") + 1]
        self.task_id = self.task_dir.name

    @property
    def behavior(self) -> dict[str, Any]:
        return self.client.behaviors[self.task_id]

    def wait(self, timeout: int | None = None, condition: str | None = None) -> dict[str, int]:
        if not self._ran:
            buffer_out = io.StringIO()
            buffer_err = io.StringIO()
            behavior = self.behavior
            if behavior.get("missing_output"):
                self._stdout = behavior.get("stdout", "")
                self._stderr = behavior.get("stderr", "")
            else:
                payload = behavior["llm_payload"]

                def llm_override(**_: Any) -> Any:
                    return payload

                with redirect_stdout(buffer_out), redirect_stderr(buffer_err):
                    worker_runtime.run_worker(
                        task_dir=self.task_dir,
                        worker_override=self.worker,
                        base_dir=self.client.base_dir,
                        llm_override=llm_override,
                    )
                self._stdout = buffer_out.getvalue() + behavior.get("stdout", "")
                self._stderr = buffer_err.getvalue() + behavior.get("stderr", "")
            self._ran = True
        return {"StatusCode": int(self.behavior.get("exit_code", 0))}

    def logs(self, stdout: bool = True, stderr: bool = True) -> bytes:
        chunks: list[str] = []
        if stdout:
            chunks.append(self._stdout)
        if stderr:
            chunks.append(self._stderr)
        return "".join(chunks).encode("utf-8")

    def remove(self, force: bool = False) -> None:
        self.removed = True
        self.client.removed_containers.append(self.name)


class FakeContainerManager:
    def __init__(self, client: "FakeDockerClient") -> None:
        self.client = client
        self.created: dict[str, FakeContainer] = {}

    def run(self, image: str, command: list[str], name: str, detach: bool, working_dir: str, environment: dict[str, str], volumes: list[str]) -> FakeContainer:  # noqa: ARG002
        container = FakeContainer(
            client=self.client,
            image=image,
            command=command,
            name=name,
            environment=environment,
        )
        self.created[name] = container
        return container

    def get(self, name: str) -> Any:
        raise RuntimeError(f"unexpected containers.get({name}) in test")


class FakeDockerClient:
    def __init__(self, base_dir: Path, behaviors: dict[str, dict[str, Any]]) -> None:
        self.base_dir = base_dir
        self.behaviors = behaviors
        self.images = FakeImages()
        self.containers = FakeContainerManager(self)
        self.removed_containers: list[str] = []


def build_task(
    *,
    task_id: str,
    worker: str,
    objective: str,
    expected_outputs: list[dict[str, str]],
    inputs: dict[str, Any] | None = None,
    constraints: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "worker": worker,
        "task_type": WORKER_TASK_TYPES[worker],
        "objective": objective,
        "inputs": inputs or {},
        "expected_outputs": expected_outputs,
        "constraints": constraints or ["must stay within contract"],
        "acceptance_criteria": acceptance_criteria or ["produce truthful output"],
    }


class ArgusHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="argus-hardening-"))
        for relative in [
            "artifacts/architecture",
            "artifacts/configs",
            "artifacts/reviews",
            "artifacts/scripts",
            "containers/worker",
            "tasks",
            "workspaces/architect",
            "workspaces/automation",
            "workspaces/critic",
            "workspaces/devops",
            "workspaces/manager",
        ]:
            (self.tmpdir / relative).mkdir(parents=True, exist_ok=True)
        (self.tmpdir / "containers" / "worker" / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
        self._old_base_dir = os.environ.get("ARGUS_BASE_DIR")
        os.environ["ARGUS_BASE_DIR"] = str(self.tmpdir)

    def tearDown(self) -> None:
        if self._old_base_dir is None:
            os.environ.pop("ARGUS_BASE_DIR", None)
        else:
            os.environ["ARGUS_BASE_DIR"] = self._old_base_dir
        shutil.rmtree(self.tmpdir)

    def _client(self, behaviors: dict[str, dict[str, Any]]) -> FakeDockerClient:
        return FakeDockerClient(self.tmpdir, behaviors)

    def test_build_worker_env_uses_selected_provider_profile(self) -> None:
        profiles_path = self.tmpdir / "contracts" / "provider_profiles.json"
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        profiles_path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "backup": {
                            "api_base": "https://backup-provider.invalid/v1",
                            "model_name": "gpt-5-codex",
                            "wire_api": "responses",
                            "api_key_env": "OPENAI_API_KEY_BACKUP",
                            "fallback_api_key_env": "OPENAI_API_KEY_FALLBACK",
                            "fallback_response_urls": [
                                "https://backup-provider.invalid/v1/responses",
                                "https://backup-provider.invalid/responses",
                            ],
                            "fallback_api_bases": ["https://backup-provider.invalid/v1"],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {
                "ARGUS_PROVIDER_PROFILE": "backup",
                "OPENAI_API_KEY": "primary-key",
                "OPENAI_API_KEY_BACKUP": "backup-key",
                "OPENAI_API_KEY_FALLBACK": "fallback-key",
                "OPENAI_API_BASE": "https://primary-provider.invalid/v1",
                "OPENAI_MODEL_NAME": "primary-model",
                "ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES": "0",
            },
            clear=False,
        ):
            env = build_worker_env("automation")

        self.assertEqual(env["OPENAI_API_KEY"], "backup-key")
        self.assertEqual(env["OPENAI_API_BASE"], "https://backup-provider.invalid/v1")
        self.assertEqual(env["OPENAI_MODEL_NAME"], "gpt-5-codex")
        self.assertEqual(env["ARGUS_LLM_WIRE_API"], "responses")
        self.assertEqual(env["ARGUS_LLM_FALLBACK_API_KEY"], "fallback-key")
        self.assertEqual(
            env["ARGUS_LLM_FALLBACK_RESPONSE_URLS"],
            "https://backup-provider.invalid/v1/responses,https://backup-provider.invalid/responses",
        )
        self.assertEqual(env["ARGUS_LLM_FALLBACK_API_BASES"], "https://backup-provider.invalid/v1")
        self.assertEqual(env["ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES"], "0")
        self.assertEqual(env["ARGUS_PROVIDER_PROFILE"], "backup")
        self.assertEqual(Path(env["ARGUS_PROVIDER_PROFILES_FILE"]).resolve(), profiles_path.resolve())

    def test_build_worker_env_profile_key_env_missing_raises(self) -> None:
        profiles_path = self.tmpdir / "contracts" / "provider_profiles.json"
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        profiles_path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "backup": {
                            "api_base": "https://backup-provider.invalid/v1",
                            "model_name": "gpt-5-codex",
                            "wire_api": "responses",
                            "api_key_env": "OPENAI_API_KEY_BACKUP_MISSING",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {
                "ARGUS_PROVIDER_PROFILE": "backup",
                "OPENAI_API_KEY": "primary-key",
                "OPENAI_API_BASE": "https://primary-provider.invalid/v1",
                "OPENAI_MODEL_NAME": "primary-model",
            },
            clear=False,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                build_worker_env("automation")

        self.assertIn("OPENAI_API_KEY_BACKUP_MISSING", str(ctx.exception))

    def test_build_worker_env_profile_fallback_key_env_missing_raises(self) -> None:
        profiles_path = self.tmpdir / "contracts" / "provider_profiles.json"
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        profiles_path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "backup": {
                            "api_base": "https://backup-provider.invalid/v1",
                            "model_name": "gpt-5-codex",
                            "wire_api": "responses",
                            "api_key_env": "OPENAI_API_KEY_BACKUP",
                            "fallback_api_key_env": "OPENAI_API_KEY_FALLBACK_MISSING",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {
                "ARGUS_PROVIDER_PROFILE": "backup",
                "OPENAI_API_KEY_BACKUP": "backup-key",
            },
            clear=False,
        ):
            with self.assertRaises(RuntimeError) as ctx:
                build_worker_env("automation")

        self.assertIn("OPENAI_API_KEY_FALLBACK_MISSING", str(ctx.exception))

    def test_build_worker_env_without_profile_keeps_legacy_env_resolution(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "primary-key",
                "OPENAI_API_BASE": "https://primary-provider.invalid/v1",
                "OPENAI_MODEL_NAME": "primary-model",
                "ARGUS_LLM_WIRE_API": "chat_completions",
            },
            clear=False,
        ):
            env = build_worker_env("automation")

        self.assertEqual(env["OPENAI_API_KEY"], "primary-key")
        self.assertEqual(env["OPENAI_API_BASE"], "https://primary-provider.invalid/v1")
        self.assertEqual(env["OPENAI_MODEL_NAME"], "primary-model")
        self.assertEqual(env["ARGUS_LLM_WIRE_API"], "chat_completions")
        self.assertNotIn("ARGUS_PROVIDER_PROFILE", env)

    def test_build_worker_env_uses_default_repo_profiles_file_when_not_overridden(self) -> None:
        profiles_path = self.tmpdir / "contracts" / "provider_profiles.json"
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        profiles_path.write_text(
            json.dumps(
                {
                    "profiles": {
                        "fast_chat_governed_baseline": {
                            "api_base": "https://fast.vpsairobot.com/v1",
                            "model_name": "gpt-5-codex",
                            "wire_api": "chat_completions",
                            "api_key_env": "OPENAI_API_KEY_FAST",
                            "fallback_chat_urls": [
                                "https://fast.vpsairobot.com/v1/chat/completions"
                            ],
                            "fallback_api_bases": ["https://fast.vpsairobot.com/v1"],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.dict(
            os.environ,
            {
                "ARGUS_PROVIDER_PROFILE": "fast_chat_governed_baseline",
                "OPENAI_API_KEY_FAST": "fast-key",
            },
            clear=False,
        ):
            os.environ.pop("ARGUS_PROVIDER_PROFILES_FILE", None)
            env = build_worker_env("automation")

        self.assertEqual(env["OPENAI_API_KEY"], "fast-key")
        self.assertEqual(env["OPENAI_API_BASE"], "https://fast.vpsairobot.com/v1")
        self.assertEqual(env["OPENAI_MODEL_NAME"], "gpt-5-codex")
        self.assertEqual(env["ARGUS_LLM_WIRE_API"], "chat_completions")
        self.assertEqual(
            env["ARGUS_LLM_FALLBACK_CHAT_URLS"],
            "https://fast.vpsairobot.com/v1/chat/completions",
        )
        self.assertEqual(env["ARGUS_LLM_FALLBACK_API_BASES"], "https://fast.vpsairobot.com/v1")
        self.assertEqual(Path(env["ARGUS_PROVIDER_PROFILES_FILE"]).resolve(), profiles_path.resolve())

    def test_failed_status_is_taken_from_output_not_exit_code(self) -> None:
        task = build_task(
            task_id="ARCH-20260319-302",
            worker="architect",
            objective="Return a deliberate contract failure for validation.",
            expected_outputs=[
                {"path": "artifacts/architecture/hardening_arch_failed_302.md", "type": "architecture"}
            ],
        )
        client = self._client(
            {
                "ARCH-20260319-302": {
                    "exit_code": 0,
                    "llm_payload": {
                        "status": "failed",
                        "summary": "Contract review failed as requested.",
                        "errors": ["Simulated contract failure."],
                    },
                }
            }
        )

        result = delegate_task(
            "architect",
            task,
            docker_client=client,
            mounts_override=[f"{self.tmpdir}:/app:rw"],
            worker_image="argus-worker:latest",
        )

        self.assertEqual(result["status"], "failed")
        record = json.loads((self.tmpdir / "tasks" / "ARCH-20260319-302.json").read_text())
        self.assertEqual(record["status"], "failed")
        runtime_log = (self.tmpdir / "workspaces" / "architect" / "ARCH-20260319-302" / "runtime.log").read_text()
        self.assertIn("exit_code: 0", runtime_log)
        self.assertIn("Simulated contract failure.", json.dumps(result, ensure_ascii=False))
        self.assertIn("argus-architect-arch-20260319-302", client.removed_containers)
        self.assertEqual(validate_output(result), [])

    def test_success_partial_and_closed_loop_outputs_are_real(self) -> None:
        partial_task = build_task(
            task_id="ARCH-20260319-303",
            worker="architect",
            objective="Produce only part of the requested hardening note set.",
            expected_outputs=[
                {"path": "artifacts/architecture/hardening_arch_partial_303.md", "type": "architecture"},
                {"path": "artifacts/architecture/hardening_arch_extra_303.md", "type": "architecture"},
            ],
        )
        auto_task = build_task(
            task_id="AUTO-20260319-401",
            worker="automation",
            objective="Generate a CLI file sync script with dry-run support.",
            expected_outputs=[
                {"path": "artifacts/scripts/closed_loop_file_sync.py", "type": "script"}
            ],
            inputs={"params": {"script_name": "closed_loop_file_sync.py"}},
            constraints=["must support --dry-run", "must run from CLI"],
            acceptance_criteria=["include --source and --destination flags"],
        )
        critic_task = build_task(
            task_id="CRITIC-20260319-402",
            worker="critic",
            objective="Review the generated file sync script for correctness and requirement fit.",
            expected_outputs=[
                {"path": "artifacts/reviews/closed_loop_file_sync_review.md", "type": "review"}
            ],
            inputs={
                "artifacts": [
                    {"path": "artifacts/scripts/closed_loop_file_sync.py", "type": "script"}
                ]
            },
            constraints=["must be grounded in the actual script artifact"],
            acceptance_criteria=["state pass/fail with evidence"],
        )

        client = self._client(
            {
                "ARCH-20260319-303": {
                    "exit_code": 0,
                    "llm_payload": {
                        "status": "partial",
                        "summary": "Produced one of two requested architecture notes.",
                        "file_contents": {
                            "artifacts/architecture/hardening_arch_partial_303.md": "# Partial hardening\n\nOnly the first document was produced.\n"
                        },
                    },
                },
                "AUTO-20260319-401": {
                    "exit_code": 0,
                    "llm_payload": {
                        "status": "success",
                        "summary": "Generated the file sync CLI script.",
                        "file_contents": {
                            "artifacts/scripts/closed_loop_file_sync.py": "#!/usr/bin/env python3\nimport argparse\nfrom pathlib import Path\n\n\ndef main() -> int:\n    parser = argparse.ArgumentParser()\n    parser.add_argument('--source', required=True)\n    parser.add_argument('--destination', required=True)\n    parser.add_argument('--dry-run', action='store_true')\n    args = parser.parse_args()\n    src = Path(args.source)\n    dst = Path(args.destination)\n    print(f'Planning sync from {src} to {dst}; dry_run={args.dry_run}')\n    print('Summary: copied=0 skipped=0')\n    return 0\n\n\nif __name__ == '__main__':\n    raise SystemExit(main())\n"
                        },
                    },
                },
                "CRITIC-20260319-402": {
                    "exit_code": 0,
                    "llm_payload": {
                        "status": "success",
                        "summary": "Reviewed the generated script and recorded findings.",
                        "file_contents": {
                            "artifacts/reviews/closed_loop_file_sync_review.md": "# Review\n\nPass. The script defines --source, --destination, and --dry-run and prints a summary line.\n"
                        },
                    },
                },
            }
        )

        partial_result = delegate_task(
            "architect",
            partial_task,
            docker_client=client,
            mounts_override=[f"{self.tmpdir}:/app:rw"],
            worker_image="argus-worker:latest",
        )
        auto_result = delegate_task(
            "automation",
            auto_task,
            docker_client=client,
            mounts_override=[f"{self.tmpdir}:/app:rw"],
            worker_image="argus-worker:latest",
        )
        critic_result = delegate_task(
            "critic",
            critic_task,
            docker_client=client,
            mounts_override=[f"{self.tmpdir}:/app:rw"],
            worker_image="argus-worker:latest",
        )

        self.assertEqual(partial_result["status"], "partial")
        self.assertTrue((self.tmpdir / "artifacts" / "architecture" / "hardening_arch_partial_303.md").exists())
        self.assertEqual(auto_result["status"], "success")
        self.assertTrue((self.tmpdir / "artifacts" / "scripts" / "closed_loop_file_sync.py").exists())
        self.assertEqual(critic_result["status"], "success")
        self.assertTrue((self.tmpdir / "artifacts" / "reviews" / "closed_loop_file_sync_review.md").exists())
        self.assertEqual(validate_output(partial_result), [])
        self.assertEqual(validate_output(auto_result), [])
        self.assertEqual(validate_output(critic_result), [])
        self.assertNotIn("artifacts_written", auto_result)

    def test_missing_output_is_closed_as_failed(self) -> None:
        task = build_task(
            task_id="ARCH-20260319-399",
            worker="architect",
            objective="Simulate a worker crash before output is written.",
            expected_outputs=[
                {"path": "artifacts/architecture/hardening_arch_missing_output_399.md", "type": "architecture"}
            ],
        )
        client = self._client(
            {
                "ARCH-20260319-399": {
                    "exit_code": 7,
                    "missing_output": True,
                    "stderr": "container crashed before output.json",
                }
            }
        )

        result = delegate_task(
            "architect",
            task,
            docker_client=client,
            mounts_override=[f"{self.tmpdir}:/app:rw"],
            worker_image="argus-worker:latest",
        )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(validate_output(result), [])
        output_path = self.tmpdir / "workspaces" / "architect" / "ARCH-20260319-399" / "output.json"
        self.assertTrue(output_path.exists())

    def test_test_mode_can_run_without_docker_client(self) -> None:
        task = build_task(
            task_id="CRITIC-20260324-001",
            worker="critic",
            objective="Produce a deterministic test-mode review without docker.",
            expected_outputs=[
                {"path": "artifacts/reviews/local_test_mode_review.md", "type": "review"}
            ],
            inputs={"artifacts": [{"path": "artifacts/scripts/example.py", "type": "script"}]},
        )

        result = delegate_task(
            "critic",
            task,
            test_mode="success",
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(validate_output(result), [])
        self.assertEqual(result.get("metadata", {}).get("scenario"), "success")
        self.assertTrue((self.tmpdir / "artifacts" / "reviews" / "local_test_mode_review.md").exists())
        runtime_log = (self.tmpdir / "workspaces" / "critic" / "CRITIC-20260324-001" / "runtime.log").read_text()
        self.assertIn("local-test-mode", runtime_log)

    def test_call_llm_uses_relaxed_default_timeout(self) -> None:
        calls: list[int] = []

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class RecordingOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:  # noqa: ARG002
                calls.append(timeout or 0)
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", RecordingOpener()):
            with mock.patch.dict(os.environ, {}, clear=False):
                content = worker_runtime.call_llm(
                    "system",
                    "user",
                    "automation",
                    {
                        "api_key": "key",
                        "api_base": "https://example.invalid/v1",
                        "chat_url": "https://example.invalid/v1/chat/completions",
                        "model_name": "demo-model",
                    },
                )

        self.assertEqual(calls, [120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_auto_falls_back_to_responses_after_http_400(self) -> None:
        calls: list[tuple[str, int]] = []

        class FakeResponse:
            def __init__(self, payload: dict[str, Any]) -> None:
                self._payload = payload

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                return json.dumps(self._payload).encode("utf-8")

        class AutoWireOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if req.full_url.endswith("/chat/completions"):
                    raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", None, None)
                return FakeResponse(
                    {
                        "id": "resp_test_123",
                        "output_text": json.dumps({"status": "success", "summary": "ok"}),
                    }
                )

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", AutoWireOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {"ARGUS_LLM_MAX_RETRIES": "2"},
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://provider.invalid/v1",
                            "chat_url": "https://provider.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://provider.invalid/v1/chat/completions",
                "https://provider.invalid/v1/responses",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_auto_fallback_tries_response_candidates_until_success(self) -> None:
        calls: list[tuple[str, int]] = []

        class FakeResponse:
            def __init__(self, payload: dict[str, Any]) -> None:
                self._payload = payload

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                return json.dumps(self._payload).encode("utf-8")

        class AutoWireCandidateOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if req.full_url.endswith("/chat/completions"):
                    raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", None, None)
                if req.full_url.endswith("/v1/responses"):
                    raise urllib.error.HTTPError(req.full_url, 502, "Bad Gateway", None, None)
                return FakeResponse(
                    {
                        "id": "resp_test_456",
                        "output_text": json.dumps({"status": "success", "summary": "ok"}),
                    }
                )

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", AutoWireCandidateOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "2",
                        "ARGUS_LLM_FALLBACK_RESPONSE_URLS": "https://provider.invalid/responses",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://provider.invalid/v1",
                            "chat_url": "https://provider.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://provider.invalid/v1/chat/completions",
                "https://provider.invalid/v1/responses",
                "https://provider.invalid/responses",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_get_llm_settings_supports_responses_wire_api(self) -> None:
        with mock.patch.object(worker_runtime, "read_secret", return_value=None):
            with mock.patch.dict(
                os.environ,
                {
                    "OPENAI_API_KEY": "key",
                    "OPENAI_API_BASE": "https://provider.invalid/v1",
                    "OPENAI_MODEL_NAME": "demo-model",
                    "ARGUS_LLM_WIRE_API": "responses",
                },
                clear=False,
            ):
                settings = worker_runtime.get_llm_settings()

        self.assertEqual(settings["wire_api"], "responses")
        self.assertEqual(settings["endpoint_url"], "https://provider.invalid/v1/responses")
        self.assertEqual(settings["chat_url"], "https://provider.invalid/v1/chat/completions")
        self.assertEqual(settings["responses_url"], "https://provider.invalid/v1/responses")

    def test_build_user_prompt_default_keeps_full_fields(self) -> None:
        task = {
            "task_id": "AUTO-TEST-001",
            "worker": "automation",
            "task_type": "generate_script",
            "objective": "obj",
            "inputs": {"x": "y" * 200},
            "constraints": ["c" * 200],
            "expected_outputs": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
            "acceptance_criteria": ["a" * 200],
            "source": {"kind": "local_inbox"},
            "metadata": {"k": "v" * 200},
        }
        with mock.patch.dict(os.environ, {"ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS": ""}, clear=False):
            prompt = worker_runtime.build_user_prompt(task)
        self.assertNotIn("truncated_for_prompt", prompt)
        self.assertIn("Prompt Compact Notes: []", prompt)

    def test_build_user_prompt_can_compact_automation_fields(self) -> None:
        task = {
            "task_id": "AUTO-TEST-002",
            "worker": "automation",
            "task_type": "generate_script",
            "objective": "obj",
            "inputs": {"x": "y" * 400},
            "constraints": ["c" * 400],
            "expected_outputs": [{"path": "artifacts/scripts/demo.py", "type": "script"}],
            "acceptance_criteria": ["a" * 400],
            "source": {"kind": "local_inbox", "blob": "s" * 400},
            "metadata": {"k": "v" * 400},
        }
        with mock.patch.dict(os.environ, {"ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS": "120"}, clear=False):
            prompt = worker_runtime.build_user_prompt(task)
        self.assertIn("truncated_for_prompt", prompt)
        self.assertIn("Prompt Compact Notes:", prompt)
        self.assertIn("inputs: truncated to 120 chars", prompt)

    def test_call_llm_honors_env_timeout_and_retry_overrides(self) -> None:
        calls: list[int] = []
        attempts = {"count": 0}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class FlakyOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:  # noqa: ARG002
                calls.append(timeout or 0)
                attempts["count"] += 1
                if attempts["count"] == 1:
                    raise TimeoutError("The read operation timed out")
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", FlakyOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {"ARGUS_LLM_TIMEOUT_SECONDS": "7", "ARGUS_LLM_MAX_RETRIES": "2"},
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://example.invalid/v1",
                            "chat_url": "https://example.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(calls, [7, 7])
        self.assertEqual(attempts["count"], 2)
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_rotates_to_fallback_chat_url_after_retryable_tls_eof(self) -> None:
        calls: list[tuple[str, int]] = []

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class FallbackOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    raise urllib.error.URLError("[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol")
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", FallbackOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "2",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_rotates_to_fallback_chat_url_after_http_403_on_primary(self) -> None:
        calls: list[tuple[str, int]] = []

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class AuthFallbackOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", AuthFallbackOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "2",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_http_403_without_fallback_remains_non_retryable(self) -> None:
        attempts = {"count": 0}

        class AlwaysForbiddenOpener:
            def open(self, req: Any, timeout: int | None = None) -> Any:  # noqa: ARG002
                attempts["count"] += 1
                raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", AlwaysForbiddenOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "",
                    },
                    clear=False,
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        worker_runtime.call_llm(
                            "system",
                            "user",
                            "automation",
                            {
                                "api_key": "key",
                                "api_base": "https://primary.invalid/v1",
                                "chat_url": "https://primary.invalid/v1/chat/completions",
                                "model_name": "demo-model",
                            },
                        )

        message = str(ctx.exception)
        self.assertIn("class=http_403", message)
        self.assertIn("attempts=1/3", message)
        self.assertEqual(attempts["count"], 1)

    def test_call_llm_quarantines_primary_after_http_403_and_retries_fallback(self) -> None:
        calls: list[tuple[str, int]] = []
        fallback_attempts = {"count": 0}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class MixedFailureOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
                fallback_attempts["count"] += 1
                if fallback_attempts["count"] == 1:
                    raise urllib.error.URLError(
                        "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol"
                    )
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", MixedFailureOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_uses_fallback_api_key_for_fallback_endpoint(self) -> None:
        calls: list[tuple[str, str | None]] = []

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class KeyAwareOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:  # noqa: ARG002
                auth = req.headers.get("Authorization")
                calls.append((req.full_url, auth))
                if "primary.invalid" in req.full_url:
                    raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", None, None)
                if auth != "Bearer fallback-key":
                    raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", None, None)
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", KeyAwareOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "primary-key",
                            "fallback_api_key": "fallback-key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _auth in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual(calls[0][1], "Bearer primary-key")
        self.assertEqual(calls[1][1], "Bearer fallback-key")
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_retries_http_520_then_recovers_after_fallback_http_401(self) -> None:
        calls: list[tuple[str, int]] = []
        primary_attempts = {"count": 0}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class MixedFailureOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    primary_attempts["count"] += 1
                    if primary_attempts["count"] == 1:
                        raise urllib.error.HTTPError(req.full_url, 520, "Web Server Returned an Unknown Error", None, None)
                    return FakeResponse()
                raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", None, None)

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", MixedFailureOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120])
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_grants_terminal_timeout_recovery_retry_after_auth_quarantine(self) -> None:
        calls: list[tuple[str, int]] = []
        primary_attempts = {"count": 0}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class TimeoutRecoveryOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    primary_attempts["count"] += 1
                    if primary_attempts["count"] == 1:
                        raise urllib.error.HTTPError(
                            req.full_url,
                            520,
                            "Web Server Returned an Unknown Error",
                            None,
                            None,
                        )
                    if primary_attempts["count"] == 2:
                        raise TimeoutError("The read operation timed out")
                    return FakeResponse()
                raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", None, None)

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", TimeoutRecoveryOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120, 120])
        self.assertEqual(primary_attempts["count"], 3)
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_grants_timeout_recovery_retry_for_http_524(self) -> None:
        calls: list[tuple[str, int]] = []
        attempts = {"count": 0}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                payload = {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps({"status": "success", "summary": "ok"})
                            }
                        }
                    ]
                }
                return json.dumps(payload).encode("utf-8")

        class GatewayTimeoutRecoveryOpener:
            def open(self, req: Any, timeout: int | None = None) -> FakeResponse:
                calls.append((req.full_url, timeout or 0))
                attempts["count"] += 1
                if attempts["count"] <= 2:
                    raise urllib.error.HTTPError(
                        req.full_url,
                        524,
                        "A timeout occurred",
                        None,
                        None,
                    )
                return FakeResponse()

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", GatewayTimeoutRecoveryOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "2",
                        "ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES": "1",
                    },
                    clear=False,
                ):
                    content = worker_runtime.call_llm(
                        "system",
                        "user",
                        "automation",
                        {
                            "api_key": "key",
                            "api_base": "https://primary.invalid/v1",
                            "chat_url": "https://primary.invalid/v1/chat/completions",
                            "model_name": "demo-model",
                        },
                    )

        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120])
        self.assertEqual(attempts["count"], 3)
        self.assertEqual(json.loads(content)["status"], "success")

    def test_call_llm_can_disable_timeout_recovery_retry(self) -> None:
        calls: list[tuple[str, int]] = []
        primary_attempts = {"count": 0}

        class TimeoutStillFailsOpener:
            def open(self, req: Any, timeout: int | None = None) -> Any:
                calls.append((req.full_url, timeout or 0))
                if "primary.invalid" in req.full_url:
                    primary_attempts["count"] += 1
                    if primary_attempts["count"] == 1:
                        raise urllib.error.HTTPError(
                            req.full_url,
                            520,
                            "Web Server Returned an Unknown Error",
                            None,
                            None,
                        )
                    raise TimeoutError("The read operation timed out")
                raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", None, None)

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", TimeoutStillFailsOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {
                        "ARGUS_LLM_MAX_RETRIES": "3",
                        "ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES": "0",
                        "ARGUS_LLM_FALLBACK_CHAT_URLS": "https://fallback.invalid/v1/chat/completions",
                    },
                    clear=False,
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        worker_runtime.call_llm(
                            "system",
                            "user",
                            "automation",
                            {
                                "api_key": "key",
                                "api_base": "https://primary.invalid/v1",
                                "chat_url": "https://primary.invalid/v1/chat/completions",
                                "model_name": "demo-model",
                            },
                        )

        message = str(ctx.exception)
        self.assertIn("class=timeout", message)
        self.assertIn("attempts=3/3", message)
        self.assertEqual(
            [url for url, _timeout in calls],
            [
                "https://primary.invalid/v1/chat/completions",
                "https://fallback.invalid/v1/chat/completions",
                "https://primary.invalid/v1/chat/completions",
            ],
        )
        self.assertEqual([timeout for _url, timeout in calls], [120, 120, 120])

    def test_classify_llm_call_error_marks_http_520_as_retryable(self) -> None:
        err = urllib.error.HTTPError("https://primary.invalid/v1/chat/completions", 520, "Unknown Error", None, None)
        error_class, retryable = worker_runtime.classify_llm_call_error(err)
        self.assertEqual(error_class, "http_520")
        self.assertTrue(retryable)

    def test_call_llm_raises_classified_tls_error_after_exhaustion(self) -> None:
        class AlwaysFailOpener:
            def open(self, req: Any, timeout: int | None = None) -> Any:  # noqa: ARG002
                raise urllib.error.URLError(
                    "[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol"
                )

        with mock.patch.object(worker_runtime, "NO_PROXY_OPENER", AlwaysFailOpener()):
            with mock.patch.object(worker_runtime.time, "sleep", return_value=None):
                with mock.patch.dict(
                    os.environ,
                    {"ARGUS_LLM_MAX_RETRIES": "2"},
                    clear=False,
                ):
                    with self.assertRaises(RuntimeError) as ctx:
                        worker_runtime.call_llm(
                            "system",
                            "user",
                            "automation",
                            {
                                "api_key": "key",
                                "api_base": "https://primary.invalid/v1",
                                "chat_url": "https://primary.invalid/v1/chat/completions",
                                "model_name": "demo-model",
                            },
                        )

        message = str(ctx.exception)
        self.assertIn("class=tls_eof", message)
        self.assertIn("attempts=2/2", message)

    def test_run_worker_repairs_invalid_json_output_once_then_succeeds(self) -> None:
        task_id = "AUTO-20260326-901"
        task_dir = self.tmpdir / "workspaces" / "automation" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        task = build_task(
            task_id=task_id,
            worker="automation",
            objective="Generate script output",
            expected_outputs=[{"path": "artifacts/scripts/repair_demo.py", "type": "script"}],
        )
        (task_dir / "task.json").write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")

        repaired_payload = json.dumps(
            {
                "status": "success",
                "summary": "Recovered valid JSON payload.",
                "file_contents": {
                    "artifacts/scripts/repair_demo.py": "print('ok')\n",
                },
            },
            ensure_ascii=False,
        )
        with mock.patch.object(
            worker_runtime,
            "get_llm_settings",
            return_value={
                "api_key": "test-key",
                "api_base": "https://example.invalid/v1",
                "chat_url": "https://example.invalid/v1/chat/completions",
                "responses_url": "https://example.invalid/v1/responses",
                "endpoint_url": "https://example.invalid/v1/chat/completions",
                "model_name": "gpt-5-codex",
                "wire_api": "chat_completions",
            },
        ):
            with mock.patch.object(worker_runtime, "load_soul", return_value="You are automation."):
                with mock.patch.object(
                    worker_runtime,
                    "call_llm",
                    side_effect=["not-json-at-all", repaired_payload],
                ) as mocked_call:
                    with mock.patch.dict(
                        os.environ,
                        {"ARGUS_LLM_JSON_REPAIR_ATTEMPTS": "1"},
                        clear=False,
                    ):
                        worker_runtime.run_worker(
                            task_dir=task_dir,
                            worker_override="automation",
                            base_dir=self.tmpdir,
                        )

        output = json.loads((task_dir / "output.json").read_text(encoding="utf-8"))
        self.assertEqual(output.get("status"), "success")
        self.assertEqual(output.get("artifacts"), [{"path": "artifacts/scripts/repair_demo.py", "type": "script"}])
        self.assertEqual(output.get("metadata", {}).get("json_output_repair_attempts_used"), 1)
        self.assertEqual(mocked_call.call_count, 2)

    def test_run_worker_json_repair_budget_zero_keeps_fail_closed(self) -> None:
        task_id = "AUTO-20260326-902"
        task_dir = self.tmpdir / "workspaces" / "automation" / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        task = build_task(
            task_id=task_id,
            worker="automation",
            objective="Generate script output",
            expected_outputs=[{"path": "artifacts/scripts/repair_demo_fail.py", "type": "script"}],
        )
        (task_dir / "task.json").write_text(json.dumps(task, ensure_ascii=False), encoding="utf-8")

        with mock.patch.object(
            worker_runtime,
            "get_llm_settings",
            return_value={
                "api_key": "test-key",
                "api_base": "https://example.invalid/v1",
                "chat_url": "https://example.invalid/v1/chat/completions",
                "responses_url": "https://example.invalid/v1/responses",
                "endpoint_url": "https://example.invalid/v1/chat/completions",
                "model_name": "gpt-5-codex",
                "wire_api": "chat_completions",
            },
        ):
            with mock.patch.object(worker_runtime, "load_soul", return_value="You are automation."):
                with mock.patch.object(worker_runtime, "call_llm", return_value="still-not-json") as mocked_call:
                    with mock.patch.dict(
                        os.environ,
                        {"ARGUS_LLM_JSON_REPAIR_ATTEMPTS": "0"},
                        clear=False,
                    ):
                        worker_runtime.run_worker(
                            task_dir=task_dir,
                            worker_override="automation",
                            base_dir=self.tmpdir,
                        )

        output = json.loads((task_dir / "output.json").read_text(encoding="utf-8"))
        self.assertEqual(output.get("status"), "failed")
        joined_errors = " | ".join(output.get("errors", []))
        self.assertIn("LLM output not valid JSON", joined_errors)
        self.assertIn("json_repair_attempts_used=0/0", joined_errors)
        self.assertEqual(mocked_call.call_count, 1)


if __name__ == "__main__":
    unittest.main()
