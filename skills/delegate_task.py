import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    import docker
    from docker.errors import ImageNotFound, NotFound
except ModuleNotFoundError:
    docker = None

    class ImageNotFound(Exception):
        pass

    class NotFound(Exception):
        pass


DEFAULT_BASE_DIR = Path("/app")
CONTAINER_APP_DIR = Path("/app")
SECRETS_DIR = Path("/run/secrets")

ALLOWED_TASK_STATES = {"pending", "running", "success", "failed", "partial"}
MAX_RETRY_ATTEMPTS = 2
DEFAULT_WORKER_IMAGE = os.environ.get("ARGUS_WORKER_IMAGE", "argus-worker:latest")
DEFAULT_WORKER_BUILD_CONTEXT = os.environ.get("ARGUS_WORKER_BUILD_CONTEXT", "/app")
DEFAULT_WORKER_DOCKERFILE = os.environ.get(
    "ARGUS_WORKER_DOCKERFILE",
    "containers/worker/Dockerfile",
)
DEFAULT_MANAGER_CONTAINER_NAME = os.environ.get(
    "ARGUS_MANAGER_CONTAINER_NAME",
    os.environ.get("ARGUS_MANAGER_CONTAINER", "manager"),
)
ARGUS_APP_HOST_PATH = os.environ.get("ARGUS_APP_HOST_PATH")
ARGUS_SECRETS_HOST_PATH = os.environ.get("ARGUS_SECRETS_HOST_PATH")
STOP_TIMEOUT_SECONDS = 5

REQUIRED_MANAGER_MOUNTS = (
    "/app/workspaces",
    "/app/artifacts",
    "/app/tasks",
    "/app/contracts",
    "/app/dispatcher",
    "/app/agents",
)

DOCKER_CLIENT = docker.from_env() if docker is not None else None


def resolve_base_dir():
    return Path(os.environ.get("ARGUS_BASE_DIR", str(DEFAULT_BASE_DIR))).resolve()


def task_root():
    return resolve_base_dir() / "tasks"


def workspace_root():
    return resolve_base_dir() / "workspaces"


def to_container_path(path):
    path = Path(path).resolve()
    base = resolve_base_dir()
    try:
        relative = path.relative_to(base)
    except ValueError:
        return str(path)
    return str(CONTAINER_APP_DIR / relative)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs():
    task_root().mkdir(parents=True, exist_ok=True)
    workspace_root().mkdir(parents=True, exist_ok=True)


def worker_dir(worker):
    path = workspace_root() / worker
    path.mkdir(parents=True, exist_ok=True)
    return path


def task_workspace_dir(worker, task_id):
    path = worker_dir(worker) / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_log_path(worker, task_id):
    return task_workspace_dir(worker, task_id) / "runtime.log"


def runtime_attempt_log_path(worker, task_id, attempt):
    return task_workspace_dir(worker, task_id) / f"runtime.attempt-{attempt}.log"


def task_file_path(task_id):
    return task_root() / f"{task_id}.json"


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


def create_task_record(task_id, worker, payload, max_retries):
    record = {
        "task_id": task_id,
        "worker": worker,
        "status": "pending",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "retries": 0,
        "max_retries": max_retries,
        "attempts": [],
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


def append_task_attempt(task_id, attempt_info):
    path = task_file_path(task_id)
    with open(path) as f:
        data = json.load(f)

    attempts = data.setdefault("attempts", [])
    attempts.append(attempt_info)
    data["retries"] = max(0, len(attempts) - 1)
    data["updated_at"] = utc_now()

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


def normalize_retry_attempts(retry_attempts):
    retries = int(retry_attempts)
    if retries < 0:
        raise RuntimeError("retry_attempts must be >= 0")
    if retries > MAX_RETRY_ATTEMPTS:
        raise RuntimeError(f"retry_attempts must be <= {MAX_RETRY_ATTEMPTS}")
    return retries


def resolve_test_mode_for_attempt(test_mode, attempt):
    if not test_mode:
        return {}

    scenario = None
    response_file = None
    if isinstance(test_mode, str):
        scenario = test_mode
    elif isinstance(test_mode, dict):
        response_file = test_mode.get("response_file")
        attempt_scenarios = test_mode.get("attempt_scenarios")
        if isinstance(attempt_scenarios, list) and attempt <= len(attempt_scenarios):
            scenario = attempt_scenarios[attempt - 1]
        else:
            scenario = test_mode.get("scenario")
    else:
        raise RuntimeError("test_mode must be None, string, or dict")

    env = {"ARGUS_TEST_MODE": "1", "ARGUS_TEST_ATTEMPT": str(attempt)}
    if scenario:
        env["ARGUS_TEST_SCENARIO"] = str(scenario)
    if response_file:
        env["ARGUS_TEST_LLM_RESPONSE_FILE"] = str(response_file)
    return env


def ensure_worker_image(docker_client, worker_image):
    try:
        docker_client.images.get(worker_image)
        return
    except Exception as e:
        text = str(e).lower()
        if not isinstance(e, ImageNotFound) and "not found" not in text:
            raise

    docker_client.images.build(
        path=DEFAULT_WORKER_BUILD_CONTEXT,
        dockerfile=DEFAULT_WORKER_DOCKERFILE,
        tag=worker_image,
        rm=True,
    )


def remove_container_if_exists(docker_client, container_name):
    try:
        stale = docker_client.containers.get(container_name)
    except Exception as e:
        text = str(e).lower()
        if isinstance(e, NotFound) or "not found" in text or "unexpected containers.get" in text:
            return
        raise
    try:
        if stale.status == "running":
            stale.stop(timeout=STOP_TIMEOUT_SECONDS)
    except Exception:
        pass
    stale.remove(force=True)


def parse_mount_spec(spec):
    parts = spec.split(":")
    if len(parts) < 2:
        raise RuntimeError(f"Invalid mount override: {spec}")
    source = parts[0]
    bind = parts[1]
    mode = parts[2] if len(parts) >= 3 else "rw"
    return source, {"bind": bind, "mode": mode}


def manager_bind_mounts(docker_client, manager_container_name, mounts_override=None):
    if mounts_override:
        parsed = {}
        for spec in mounts_override:
            source, data = parse_mount_spec(spec)
            parsed[source] = data
        return parsed

    if ARGUS_APP_HOST_PATH:
        binds = {ARGUS_APP_HOST_PATH: {"bind": "/app", "mode": "rw"}}
        if ARGUS_SECRETS_HOST_PATH:
            binds[ARGUS_SECRETS_HOST_PATH] = {"bind": "/run/secrets", "mode": "ro"}
        return binds

    manager = docker_client.containers.get(manager_container_name)
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
            f"Manager container {manager_container_name} is missing required mounts: {missing_text}"
        )
    return bind_mounts


def start_worker_oneshot(
    docker_client,
    worker,
    task_dir,
    task_id,
    attempt,
    *,
    test_mode=None,
    mounts_override=None,
    worker_image=None,
):
    image_name = worker_image or DEFAULT_WORKER_IMAGE
    ensure_worker_image(docker_client, image_name)
    container_name = one_shot_container_name(worker, task_id)
    remove_container_if_exists(docker_client, container_name)

    command = [
        "python",
        "/app/dispatcher/worker_runtime.py",
        "--task-dir",
        to_container_path(task_dir),
        "--worker",
        worker,
    ]

    env = build_worker_env(worker)
    env.update(resolve_test_mode_for_attempt(test_mode, attempt))

    run_kwargs = {
        "image": image_name,
        "name": container_name,
        "command": command,
        "working_dir": "/app",
        "detach": True,
        "remove": False,
        "volumes": manager_bind_mounts(
            docker_client,
            DEFAULT_MANAGER_CONTAINER_NAME,
            mounts_override=mounts_override,
        ),
        "environment": env,
        "labels": {
            "argus.oneshot": "true",
            "argus.worker": worker,
            "argus.task_id": task_id,
            "argus.attempt": str(attempt),
        },
    }
    try:
        container = docker_client.containers.run(**run_kwargs)
    except TypeError as e:
        # Test doubles may not implement Docker SDK's full run() kwargs.
        if "unexpected keyword argument" not in str(e):
            raise
        fallback_kwargs = dict(run_kwargs)
        fallback_kwargs.pop("remove", None)
        fallback_kwargs.pop("labels", None)
        container = docker_client.containers.run(**fallback_kwargs)
    return container


def cleanup_worker_container(container):
    if container is None:
        return
    status = None
    try:
        container.reload()
        status = getattr(container, "status", None)
    except Exception:
        status = getattr(container, "status", None)
    if status == "running":
        try:
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


def write_runtime_logs(
    worker,
    task_id,
    attempt,
    container_name,
    worker_image,
    started_at,
    wait_info,
    stdout_text,
    stderr_text,
):
    lines = [
        f"task_id: {task_id}",
        f"worker: {worker}",
        f"attempt: {attempt}",
        f"container_name: {container_name}",
        f"worker_image: {worker_image}",
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
    content = "\n".join(lines)
    attempt_path = runtime_attempt_log_path(worker, task_id, attempt)
    latest_path = runtime_log_path(worker, task_id)
    attempt_path.write_text(content)
    latest_path.write_text(content)
    return attempt_path, latest_path


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


def first_result_error(result):
    errors = result.get("errors")
    if isinstance(errors, list) and errors:
        return str(errors[0])
    return None


def is_retryable_output_failure(result):
    if str(result.get("status", "")).strip().lower() != "failed":
        return False
    errors = result.get("errors")
    if not isinstance(errors, list):
        return False
    for error in errors:
        if str(error).strip().lower().startswith("transient:"):
            return True
    return False


def build_delegate_failure_output(task_id, worker, attempt, error_message):
    return {
        "task_id": task_id,
        "worker": worker,
        "status": "failed",
        "summary": "Worker execution failed before a valid output.json was available.",
        "artifacts": [],
        "errors": [str(error_message)],
        "metadata": {
            "delegate_failure": True,
            "attempt": attempt,
        },
        "timestamp": utc_now(),
    }


def write_fallback_output(worker, task_id, payload):
    output_path = task_workspace_dir(worker, task_id) / "output.json"
    with open(output_path, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return output_path


def delegate_task(
    worker: str,
    payload: dict,
    timeout: int = 600,
    retry_attempts: int = 0,
    test_mode=None,
    docker_client=None,
    mounts_override=None,
    worker_image=None,
):
    ensure_dirs()
    task_id = validate_payload(worker, payload)
    retries = normalize_retry_attempts(retry_attempts)
    max_attempts = 1 + retries
    payload = {**payload, "worker": worker}
    task_dir = task_workspace_dir(worker, task_id)
    container_name = one_shot_container_name(worker, task_id)
    image_name = worker_image or DEFAULT_WORKER_IMAGE
    if docker_client is None and DOCKER_CLIENT is None:
        raise RuntimeError(
            "docker SDK for Python is not available. Install `docker` or pass docker_client."
        )
    client = docker_client or DOCKER_CLIENT

    create_task_record(task_id, worker, payload, max_retries=retries)
    update_task_status(task_id, "running")

    for attempt in range(1, max_attempts + 1):
        write_worker_task(worker, task_id, payload)
        clear_old_output(worker, task_id)
        started_at = utc_now()
        wait_info = {
            "exit_code": None,
            "timed_out": False,
            "wait_error": None,
            "finished_at": None,
        }
        stdout_text = ""
        stderr_text = ""
        worker_container = None
        runtime_attempt_log = runtime_attempt_log_path(worker, task_id, attempt)

        try:
            worker_container = start_worker_oneshot(
                client,
                worker,
                task_dir,
                task_id,
                attempt,
                test_mode=test_mode,
                mounts_override=mounts_override,
                worker_image=image_name,
            )
            wait_info = wait_container_exit(worker_container, timeout=timeout)
            stdout_text = container_text_logs(worker_container, stdout=True, stderr=False)
            stderr_text = container_text_logs(worker_container, stdout=False, stderr=True)
        except Exception as e:
            wait_info["wait_error"] = wait_info["wait_error"] or f"Container start failure: {e}"
        finally:
            runtime_attempt_log, _ = write_runtime_logs(
                worker,
                task_id,
                attempt,
                container_name,
                image_name,
                started_at,
                wait_info,
                stdout_text,
                stderr_text,
            )
            cleanup_worker_container(worker_container)

        result, output_error = read_worker_output_once(worker, task_id)

        if result is None:
            output_issue = output_error or "Worker exited without producing output.json"
            if "Missing output.json" in output_issue:
                output_issue = (
                    "Worker exited without producing output.json "
                    f"({output_issue})"
                )
            message_parts = [output_issue]
            if wait_info.get("timed_out"):
                message_parts.append("Worker timeout")
            if wait_info.get("wait_error"):
                message_parts.append(wait_info["wait_error"])
            message_parts.append(f"runtime_log={runtime_attempt_log}")
            message = "; ".join(message_parts)
            fallback = build_delegate_failure_output(task_id, worker, attempt, message)
            write_fallback_output(worker, task_id, fallback)
            retryable = True
            append_task_attempt(
                task_id,
                {
                    "attempt": attempt,
                    "status": "failed",
                    "retryable": retryable,
                    "error": message,
                    "runtime_log": str(runtime_attempt_log),
                    "exit_code": wait_info.get("exit_code"),
                    "timed_out": wait_info.get("timed_out"),
                    "wait_error": wait_info.get("wait_error"),
                    "output_path": str(task_dir / "output.json"),
                    "started_at": started_at,
                    "finished_at": wait_info.get("finished_at"),
                },
            )
            if retryable and attempt < max_attempts:
                continue
            update_task_status(task_id, "failed", result=fallback, error_message=message)
            return fallback

        if result.get("task_id") != task_id:
            message = (
                f"Mismatched output task_id={result.get('task_id')} expected={task_id}; "
                f"runtime_log={runtime_attempt_log}"
            )
            fallback = build_delegate_failure_output(task_id, worker, attempt, message)
            write_fallback_output(worker, task_id, fallback)
            append_task_attempt(
                task_id,
                {
                    "attempt": attempt,
                    "status": "failed",
                    "retryable": False,
                    "error": message,
                    "runtime_log": str(runtime_attempt_log),
                    "exit_code": wait_info.get("exit_code"),
                    "timed_out": wait_info.get("timed_out"),
                    "wait_error": wait_info.get("wait_error"),
                    "output_path": str(task_dir / "output.json"),
                    "started_at": started_at,
                    "finished_at": wait_info.get("finished_at"),
                },
            )
            update_task_status(task_id, "failed", result=fallback, error_message=message)
            return fallback

        task_state = result_to_task_state(result)
        retryable = is_retryable_output_failure(result)
        append_task_attempt(
            task_id,
            {
                "attempt": attempt,
                "status": task_state,
                "retryable": retryable,
                "error": first_result_error(result),
                "runtime_log": str(runtime_attempt_log),
                "exit_code": wait_info.get("exit_code"),
                "timed_out": wait_info.get("timed_out"),
                "wait_error": wait_info.get("wait_error"),
                "output_path": str(task_dir / "output.json"),
                "started_at": started_at,
                "finished_at": wait_info.get("finished_at"),
            },
        )

        if task_state == "failed" and retryable and attempt < max_attempts:
            continue

        update_task_status(
            task_id,
            task_state,
            result=result,
            error_message=first_result_error(result) if task_state == "failed" else None,
        )
        return result

    final_message = "Worker attempts exhausted without a terminal output."
    fallback = build_delegate_failure_output(task_id, worker, max_attempts, final_message)
    write_fallback_output(worker, task_id, fallback)
    update_task_status(task_id, "failed", result=fallback, error_message=final_message)
    return fallback
