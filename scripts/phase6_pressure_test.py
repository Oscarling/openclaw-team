#!/usr/bin/env python3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import docker

sys.path.insert(0, "/app")

from dispatcher.worker_runtime import load_output_schema, validate_output_against_schema
from skills.delegate_task import delegate_task

BASE_DIR = Path("/app")
TASKS_DIR = BASE_DIR / "tasks"
WORKSPACES_DIR = BASE_DIR / "workspaces"
REPORT_PATH = BASE_DIR / "PHASE6_STABILITY_REPORT.md"


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_task(worker, task_id, task_type, objective, expected_outputs, inputs=None, constraints=None):
    return {
        "task_id": task_id,
        "worker": worker,
        "task_type": task_type,
        "objective": objective,
        "inputs": inputs or {},
        "expected_outputs": expected_outputs,
        "constraints": constraints or ["phase6 pressure test constraint"],
        "source": {"kind": "manual", "card_title": "phase6_pressure"},
        "metadata": {"phase": "phase6", "suite": "pressure"},
    }


def task_paths(worker, task_id):
    task_dir = WORKSPACES_DIR / worker / task_id
    return {
        "task_record": TASKS_DIR / f"{task_id}.json",
        "task_json": task_dir / "task.json",
        "output_json": task_dir / "output.json",
        "runtime_log": task_dir / "runtime.log",
    }


def run_case(case, schema):
    payload = case["payload"]
    result = delegate_task(
        case["worker"],
        payload,
        timeout=case.get("timeout", 180),
        retry_attempts=case.get("retry_attempts", 0),
        test_mode=case.get("test_mode"),
    )
    paths = task_paths(case["worker"], payload["task_id"])
    checks = []

    for key, path in paths.items():
        checks.append((f"{key} exists", path.exists()))

    schema_errors = validate_output_against_schema(result, schema)
    checks.append(("output schema valid", len(schema_errors) == 0))
    checks.append(("status matches expected", result.get("status") == case["expected_status"]))

    if paths["task_record"].exists():
        task_record = json.loads(paths["task_record"].read_text())
        checks.append(("task.status equals output.status", task_record.get("status") == result.get("status")))
    else:
        checks.append(("task.status equals output.status", False))

    if result.get("status") in {"success", "partial"}:
        artifact_ok = True
        for artifact in result.get("artifacts", []):
            artifact_path = BASE_DIR / artifact["path"]
            artifact_ok = artifact_ok and artifact_path.exists()
        checks.append(("artifacts exist", artifact_ok and len(result.get("artifacts", [])) > 0))
    else:
        checks.append(("artifacts exist", True))

    ok = all(flag for _, flag in checks)
    return {
        "task_id": payload["task_id"],
        "worker": case["worker"],
        "expected_status": case["expected_status"],
        "actual_status": result.get("status"),
        "retry_attempts": case.get("retry_attempts", 0),
        "checks": checks,
        "schema_errors": schema_errors,
        "result": result,
        "paths": {k: str(v) for k, v in paths.items()},
        "ok": ok,
    }


def format_checks(checks):
    lines = []
    for label, status in checks:
        mark = "PASS" if status else "FAIL"
        lines.append(f"- {mark} {label}")
    return "\n".join(lines)


def no_shared_workspace_files():
    offenders = []
    for worker in ("architect", "devops", "automation", "critic"):
        for filename in ("task.json", "output.json"):
            candidate = WORKSPACES_DIR / worker / filename
            if candidate.exists():
                offenders.append(str(candidate))
    return offenders


def no_leftover_oneshot_containers():
    client = docker.from_env()
    leftovers = client.containers.list(all=True, filters={"label": "argus.oneshot=true"})
    return [container.name for container in leftovers]


def main():
    schema = load_output_schema()
    cases = [
        {
            "worker": "architect",
            "expected_status": "success",
            "test_mode": "success",
            "payload": build_task(
                "architect",
                "ARCH-20260319-610",
                "design_architecture",
                "Create a minimal architecture note for pressure suite success.",
                [{"path": "artifacts/architecture/phase6_pressure_arch_success_610.md", "type": "architecture"}],
            ),
        },
        {
            "worker": "architect",
            "expected_status": "failed",
            "test_mode": "failed",
            "payload": build_task(
                "architect",
                "ARCH-20260319-611",
                "design_architecture",
                "Force a failed output for pressure suite.",
                [{"path": "artifacts/architecture/phase6_pressure_arch_failed_611.md", "type": "architecture"}],
            ),
        },
        {
            "worker": "architect",
            "expected_status": "partial",
            "test_mode": "partial",
            "payload": build_task(
                "architect",
                "ARCH-20260319-612",
                "design_architecture",
                "Force a partial output for pressure suite.",
                [
                    {"path": "artifacts/architecture/phase6_pressure_arch_partial_612.md", "type": "architecture"},
                    {"path": "artifacts/architecture/phase6_pressure_arch_extra_612.md", "type": "architecture"},
                ],
            ),
        },
        {
            "worker": "automation",
            "expected_status": "success",
            "test_mode": "success",
            "payload": build_task(
                "automation",
                "AUTO-20260319-613",
                "generate_script",
                "Generate first pressure script artifact.",
                [{"path": "artifacts/scripts/phase6_pressure_auto_613.py", "type": "script"}],
                inputs={"params": {"script_name": "phase6_pressure_auto_613.py"}},
            ),
        },
        {
            "worker": "critic",
            "expected_status": "success",
            "test_mode": "success",
            "payload": build_task(
                "critic",
                "CRITIC-20260319-615",
                "review_artifact",
                "Review first pressure script artifact.",
                [{"path": "artifacts/reviews/phase6_pressure_review_615.md", "type": "review"}],
                inputs={"artifacts": [{"path": "artifacts/scripts/phase6_pressure_auto_613.py", "type": "script"}]},
            ),
        },
        {
            "worker": "automation",
            "expected_status": "success",
            "test_mode": "success",
            "payload": build_task(
                "automation",
                "AUTO-20260319-614",
                "generate_script",
                "Generate second pressure script artifact.",
                [{"path": "artifacts/scripts/phase6_pressure_auto_614.py", "type": "script"}],
                inputs={"params": {"script_name": "phase6_pressure_auto_614.py"}},
            ),
        },
        {
            "worker": "critic",
            "expected_status": "success",
            "test_mode": "success",
            "payload": build_task(
                "critic",
                "CRITIC-20260319-616",
                "review_artifact",
                "Review second pressure script artifact.",
                [{"path": "artifacts/reviews/phase6_pressure_review_616.md", "type": "review"}],
                inputs={"artifacts": [{"path": "artifacts/scripts/phase6_pressure_auto_614.py", "type": "script"}]},
            ),
        },
        {
            "worker": "architect",
            "expected_status": "success",
            "retry_attempts": 1,
            "test_mode": {"attempt_scenarios": ["transient_failed", "success"]},
            "payload": build_task(
                "architect",
                "ARCH-20260319-617",
                "design_architecture",
                "Validate bounded retry behavior by forcing transient failure first.",
                [{"path": "artifacts/architecture/phase6_pressure_arch_retry_617.md", "type": "architecture"}],
            ),
        },
    ]

    results = [run_case(case, schema) for case in cases]

    shared_workspace_offenders = no_shared_workspace_files()
    leftover_containers = no_leftover_oneshot_containers()

    duplicate_artifacts = []
    seen_artifacts = set()
    for item in results:
        for artifact in item["result"].get("artifacts", []):
            path = artifact["path"]
            if path in seen_artifacts:
                duplicate_artifacts.append(path)
            seen_artifacts.add(path)

    all_ok = True
    for item in results:
        all_ok = all_ok and item["ok"]
    all_ok = all_ok and not shared_workspace_offenders
    all_ok = all_ok and not leftover_containers
    all_ok = all_ok and not duplicate_artifacts

    lines = [
        "# Phase 6 Stability Report",
        "",
        f"- Generated at: {utc_now()}",
        f"- Total tasks: {len(results)}",
        f"- Overall result: {'PASS' if all_ok else 'FAIL'}",
        "",
        "## Global Checks",
        f"- Shared workspace task/output files present: {'NO' if not shared_workspace_offenders else 'YES'}",
        f"- Leftover argus one-shot containers: {len(leftover_containers)}",
        f"- Duplicate artifact paths: {len(duplicate_artifacts)}",
        "",
    ]
    if shared_workspace_offenders:
        lines.append("### Shared Workspace Offenders")
        for path in shared_workspace_offenders:
            lines.append(f"- {path}")
        lines.append("")
    if leftover_containers:
        lines.append("### Leftover One-shot Containers")
        for name in leftover_containers:
            lines.append(f"- {name}")
        lines.append("")
    if duplicate_artifacts:
        lines.append("### Duplicate Artifact Paths")
        for path in duplicate_artifacts:
            lines.append(f"- {path}")
        lines.append("")

    lines.append("## Task Results")
    for item in results:
        lines.extend(
            [
                "",
                f"### {item['task_id']} ({item['worker']})",
                f"- Expected status: {item['expected_status']}",
                f"- Actual status: {item['actual_status']}",
                f"- Retry attempts configured: {item['retry_attempts']}",
                f"- Result: {'PASS' if item['ok'] else 'FAIL'}",
                "- Checks:",
                format_checks(item["checks"]),
                "- Paths:",
                f"  task_record: {item['paths']['task_record']}",
                f"  task_json: {item['paths']['task_json']}",
                f"  output_json: {item['paths']['output_json']}",
                f"  runtime_log: {item['paths']['runtime_log']}",
            ]
        )
        if item["schema_errors"]:
            lines.append("- Schema errors:")
            for err in item["schema_errors"]:
                lines.append(f"  - {err}")

    REPORT_PATH.write_text("\n".join(lines) + "\n")
    print(json.dumps({"report_path": str(REPORT_PATH), "overall_pass": all_ok}, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
