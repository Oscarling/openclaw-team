import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import docker
from docker.errors import ImageNotFound, NotFound


BASE_DIR = Path("/app")
TASK_DIR = BASE_DIR / "tasks"
WORKSPACE_DIR = BASE_DIR / "workspaces"
SECRETS_DIR = Path("/run/secrets")
ALLOWED_TASK_STATES = {"pending", "running", "success", "failed", "partial"}
WORKER_IMAGE = os.environ.get("ARGUS_WORKER_IMAGE", "argus-worker:latest")
WORKER_BUILD_CONTEXT = os.environ.get("ARGUS_WORKER_BUILD_CONTEXT", "/app")
WORKER_DOCKERFILE = os.environ.get("ARGUS_WORKER_DOCKERFILE", "containers/worker/Dockerfile")
MANAGER_CONTAINER_NAME = os.environ.get("ARGUS_MANAGER_CONTAINER", "manager")
STOP_TIMEOUT_SECONDS = 5
REQUIRED_MANAGER_MOUNTS = (
    "/app/workspaces",
    "/app/artifacts",
    "/app/tasks",
    "/app/contracts",
    "/app/dispatcher",
    "/app/agents",
)

client = docker.from_env()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs():
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def worker_dir(worker):
    path = WORKSPACE_DIR / worker
    path.mkdir(parents=True, exist_ok=True)
    return path


def task_workspace_dir(worker, task_id):
    path = worker_dir(worker) / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_log_path(worker, task_id):
    return task_workspace_dir(worker, task_id) / "runtime.log"


def task_file_path(task_id):
    return TASK_DIR / f"{task_id}.json"


def write_worker_task(worker, task_id, payload):
    path = task_workspace_dir(worker, task_id) / "task.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def clear_old_output(worker, task_id):
    output_file = task_workspace_dir(worker, task_id) / "output.json"
    if output_file.exists():
        output_file.unlink()


def read_worker_output_once(worker, task_id):
    output_file = task_workspace_dir(worker, task_id) / "output.json"
    if not output_file.exists():
        return None, f"Missing output.json at {output_file}"
    try:
        with open(output_file) as f:
            return json.load(f), None
    except Exception as e:
        return None, f"Failed parsing output.json: {e}"


def create_task_record(task_id, worker, payload):
    record = {
        "task_id": task_id,
        "worker": worker,
        "status": "pending",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "retries": 0,
        "max_retries": 3,
        "task_dir": str(task_workspace_dir(worker, task_id)),
        "payload": payload,
    }
    with open(task_file_path(task_id), "w") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return record


def update_task_status(task_id, status, result=None, error_message=None):
    if status not in ALLOWED_TASK_STATES:
        raise RuntimeError(f"Unsupported task status: {status}")

    path = task_file_path(task_id)
    with open(path) as f:
        data = json.load(f)

    data["status"] = status
    data["updated_at"] = utc_now()
    if result is not None:
        data["result"] = result
    if error_message:
        data["error"] = error_message

    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def sanitize_task_id(task_id):
    return re.sub(r"[^a-zA-Z0-9_.-]", "-", task_id)


def one_shot_container_name(worker, task_id):
    safe_task = sanitize_task_id(task_id).lower()
    safe_worker = re.sub(r"[^a-zA-Z0-9_.-]", "-", worker).lower()
    return f"argus-{safe_worker}-{safe_task}"


def read_secret(*names):
    for name in names:
        path = SECRETS_DIR / name
        if path.exists():
            value = path.read_text().strip()
            if value:
                return value
    return None


def first_env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return None


def build_worker_env(worker):
    env = {
        "WORKER_NAME": worker,
        "HTTP_PROXY": "",
        "HTTPS_PROXY": "",
        "http_proxy": "",
        "https_proxy": "",
        "NO_PROXY": "localhost,127.0.0.1",
        "no_proxy": "localhost,127.0.0.1",
    }
    env["OPENAI_API_KEY"] = read_secret("openai_api_key", "api_key") or first_env(
        "OPENAI_API_KEY",
        "API_KEY",
    )
    env["OPENAI_API_BASE"] = read_secret("openai_api_base", "api_base") or first_env(
        "OPENAI_API_BASE",
        "API_BASE",
    )
    env["OPENAI_MODEL_NAME"] = read_secret(
        "openai_model_name",
        "model_name",
    ) or first_env(
        "OPENAI_MODEL_NAME",
        "MODEL_NAME",
        "LLM_MODEL_NAME",
        "LLM_MODEL",
        "MODEL",
    )
    return {key: value for key, value in env.items() if value is not None}


def ensure_worker_image():
    try:
        client.images.get(WORKER_IMAGE)
        return
    except ImageNotFound:
        pass

    client.images.build(
        path=WORKER_BUILD_CONTEXT,
        dockerfile=WORKER_DOCKERFILE,
        tag=WORKER_IMAGE,
        rm=True,
    )


def remove_container_if_exists(container_name):
    try:
        stale = client.containers.get(container_name)
    except NotFound:
        return
    try:
        if stale.status == "running":
            stale.stop(timeout=STOP_TIMEOUT_SECONDS)
    except Exception:
        pass
    stale.remove(force=True)


def manager_bind_mounts():
    manager = client.containers.get(MANAGER_CONTAINER_NAME)
    manager.reload()
    required = set(REQUIRED_MANAGER_MOUNTS)
    bind_mounts = {}
    found = set()

    for mount in manager.attrs.get("Mounts", []):
        destination = mount.get("Destination")
        source = mount.get("Source")
        if destination not in required or not source:
            continue
        found.add(destination)
        bind_mounts[source] = {
            "bind": destination,
            "mode": "rw" if mount.get("RW", True) else "ro",
        }

    missing = sorted(required - found)
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(
            f"Manager container {MANAGER_CONTAINER_NAME} is missing required mounts: {missing_text}"
        )
    return bind_mounts


def start_worker_oneshot(worker, task_dir, task_id):
    ensure_worker_image()
    container_name = one_shot_container_name(worker, task_id)
    remove_container_if_exists(container_name)

    command = [
        "python",
        "/app/dispatcher/worker_runtime.py",
        "--task-dir",
        str(task_dir),
        "--worker",
        worker,
    ]

    container = client.containers.run(
        image=WORKER_IMAGE,
        name=container_name,
        command=command,
        working_dir="/app",
        detach=True,
        remove=False,
        volumes=manager_bind_mounts(),
        environment=build_worker_env(worker),
        labels={
            "argus.oneshot": "true",
            "argus.worker": worker,
            "argus.task_id": task_id,
        },
    )
    return container


def cleanup_worker_container(container):
    if container is None:
        return
    try:
        container.reload()
    except Exception:
        return
    try:
        if container.status == "running":
            container.stop(timeout=STOP_TIMEOUT_SECONDS)
    except Exception:
        pass
    try:
        container.remove(force=True)
    except Exception:
        pass


def container_text_logs(container, stdout, stderr):
    try:
        raw = container.logs(stdout=stdout, stderr=stderr)
        return raw.decode("utf-8", "ignore")
    except Exception as e:
        return f"<unable to read {'stdout' if stdout else 'stderr'} logs: {e}>"


def write_runtime_log(worker, task_id, container_name, started_at, wait_info, stdout_text, stderr_text):
    path = runtime_log_path(worker, task_id)
    lines = [
        f"task_id: {task_id}",
        f"worker: {worker}",
        f"container_name: {container_name}",
        f"worker_image: {WORKER_IMAGE}",
        f"started_at: {started_at}",
        f"finished_at: {wait_info.get('finished_at')}",
        f"exit_code: {wait_info.get('exit_code')}",
        f"timed_out: {wait_info.get('timed_out')}",
        f"wait_error: {wait_info.get('wait_error') or ''}",
        "",
        "=== stdout ===",
        stdout_text.rstrip(),
        "",
        "=== stderr ===",
        stderr_text.rstrip(),
        "",
    ]
    path.write_text("\n".join(lines))
    return path


def wait_container_exit(container, timeout):
    wait_info = {
        "exit_code": None,
        "timed_out": False,
        "wait_error": None,
        "finished_at": None,
    }
    try:
        result = container.wait(timeout=timeout, condition="not-running")
        wait_info["exit_code"] = result.get("StatusCode")
    except Exception as e:
        message = str(e)
        if "Read timed out" in message or "ReadTimeout" in message:
            wait_info["timed_out"] = True
            wait_info["wait_error"] = "Worker timeout"
            try:
                container.stop(timeout=STOP_TIMEOUT_SECONDS)
            except Exception:
                pass
        else:
            wait_info["wait_error"] = f"Failed waiting container completion: {message}"
    wait_info["finished_at"] = utc_now()
    return wait_info


def validate_payload(worker, payload):
    if not isinstance(payload, dict):
        raise RuntimeError("payload must be a dict")
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise RuntimeError("payload.task_id is required")
    payload_worker = payload.get("worker", worker)
    if payload_worker != worker:
        raise RuntimeError("payload.worker must match delegate target worker")
    if "expected_outputs" not in payload:
        raise RuntimeError("payload.expected_outputs is required")
    if "constraints" not in payload:
        raise RuntimeError("payload.constraints is required")
    if "task_type" not in payload:
        raise RuntimeError("payload.task_type is required")
    return task_id


def result_to_task_state(result):
    status = str(result.get("status", "")).strip().lower()
    if status == "success":
        return "success"
    if status == "partial":
        return "partial"
    return "failed"


def delegate_task(worker: str, payload: dict, timeout: int = 600):
    ensure_dirs()
    task_id = validate_payload(worker, payload)
    payload = {**payload, "worker": worker}
    task_dir = task_workspace_dir(worker, task_id)
    worker_container = None
    container_name = one_shot_container_name(worker, task_id)
    started_at = utc_now()

    create_task_record(task_id, worker, payload)
    write_worker_task(worker, task_id, payload)
    clear_old_output(worker, task_id)
    update_task_status(task_id, "running")

    try:
        worker_container = start_worker_oneshot(worker, task_dir, task_id)
    except Exception as e:
        wait_info = {
            "exit_code": None,
            "timed_out": False,
            "wait_error": f"Failed to start one-shot worker container: {e}",
            "finished_at": utc_now(),
        }
        write_runtime_log(worker, task_id, container_name, started_at, wait_info, "", "")
        update_task_status(task_id, "failed", error_message=wait_info["wait_error"])
        raise RuntimeError(wait_info["wait_error"]) from e

    try:
        wait_info = wait_container_exit(worker_container, timeout=timeout)
        stdout_text = container_text_logs(worker_container, stdout=True, stderr=False)
        stderr_text = container_text_logs(worker_container, stdout=False, stderr=True)
        log_file = write_runtime_log(
            worker,
            task_id,
            container_name,
            started_at,
            wait_info,
            stdout_text,
            stderr_text,
        )

        result, output_error = read_worker_output_once(worker, task_id)
        if result is None:
            details = [output_error]
            if wait_info.get("timed_out"):
                details.append("Worker timeout")
            if wait_info.get("wait_error"):
                details.append(wait_info["wait_error"])
            details.append(f"exit_code={wait_info.get('exit_code')}")
            details.append(f"runtime_log={log_file}")
            message = "; ".join(details)
            update_task_status(task_id, "failed", error_message=message)
            raise RuntimeError(message)

        if result.get("task_id") != task_id:
            message = (
                f"Mismatched output task_id={result.get('task_id')} expected={task_id}; "
                f"runtime_log={log_file}"
            )
            update_task_status(task_id, "failed", error_message=message)
            raise RuntimeError(message)

        task_state = result_to_task_state(result)
        update_task_status(task_id, task_state, result=result)
        return result
    finally:
        cleanup_worker_container(worker_container)
