from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

sys.path.insert(0, "/app/workspace")

from argus_contracts import validate_output  # noqa: E402
from dispatcher import worker_runtime  # noqa: E402
from skills.delegate_task import delegate_task  # noqa: E402

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
        output_data = json.loads(output_path.read_text())
        self.assertIn("without producing output.json", json.dumps(output_data, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
