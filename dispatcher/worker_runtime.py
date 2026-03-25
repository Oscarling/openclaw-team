import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ==========================================
# Path configuration
# ==========================================
DEFAULT_BASE_DIR = Path("/app")
BASE_DIR = DEFAULT_BASE_DIR
ARTIFACT_DIR = BASE_DIR / "artifacts"
AGENT_DIR = BASE_DIR / "agents"
CONTRACT_DIR = BASE_DIR / "contracts"
SECRETS_DIR = Path("/run/secrets")
OUTPUT_SCHEMA_PATH = CONTRACT_DIR / "output.schema.json"


def resolve_base_dir(base_dir=None):
    if base_dir is None:
        base_dir = os.environ.get("ARGUS_BASE_DIR", str(DEFAULT_BASE_DIR))
    return Path(base_dir).resolve()


def configure_paths(base_dir=None):
    global BASE_DIR, ARTIFACT_DIR, AGENT_DIR, CONTRACT_DIR, OUTPUT_SCHEMA_PATH
    BASE_DIR = resolve_base_dir(base_dir)
    ARTIFACT_DIR = BASE_DIR / "artifacts"
    AGENT_DIR = BASE_DIR / "agents"
    CONTRACT_DIR = BASE_DIR / "contracts"
    OUTPUT_SCHEMA_PATH = CONTRACT_DIR / "output.schema.json"


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


def require_setting(label, secret_names, env_names):
    value = read_secret(*secret_names)
    if value:
        return value
    value = first_env(*env_names)
    if value:
        return value
    joined = ", ".join([*secret_names, *env_names])
    raise RuntimeError(f"Missing {label}. Checked: {joined}")


def read_int_env(name, default, *, minimum=1):
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer when set") from exc
    if value < minimum:
        raise RuntimeError(f"{name} must be >= {minimum}")
    return value


# ==========================================
# Runtime guards
# ==========================================
DEFAULT_LLM_TIMEOUT_SECONDS = 120
DEFAULT_LLM_MAX_RETRIES = 3
MAX_ARTIFACT_SIZE = 2 * 1024 * 1024  # 2MB
NO_PROXY_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
HTTP_USER_AGENT = "Mozilla/5.0"
ALLOWED_STATUSES = {"success", "failed", "partial"}
ARTIFACT_TYPE_BY_PREFIX = {
    "artifacts/architecture/": "architecture",
    "artifacts/scripts/": "script",
    "artifacts/configs/": "config",
    "artifacts/reviews/": "review",
}
DEFAULT_ARTIFACT_TYPE = "doc"
TEST_MODE_ENV = "ARGUS_TEST_MODE"
TEST_SCENARIO_ENV = "ARGUS_TEST_SCENARIO"
TEST_RESPONSE_FILE_ENV = "ARGUS_TEST_LLM_RESPONSE_FILE"


def normalize_chat_endpoint(api_base):
    base = api_base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def get_llm_settings():
    api_key = require_setting(
        "API key",
        ("openai_api_key", "api_key"),
        ("OPENAI_API_KEY", "API_KEY"),
    )
    api_base = require_setting(
        "API base URL",
        ("openai_api_base", "api_base"),
        ("OPENAI_API_BASE", "API_BASE"),
    )
    model_name = require_setting(
        "model name",
        ("openai_model_name", "model_name"),
        ("OPENAI_MODEL_NAME", "MODEL_NAME", "LLM_MODEL_NAME", "LLM_MODEL", "MODEL"),
    )
    return {
        "api_key": api_key,
        "api_base": api_base,
        "chat_url": normalize_chat_endpoint(api_base),
        "model_name": model_name,
    }


def llm_timeout_seconds():
    return read_int_env(
        "ARGUS_LLM_TIMEOUT_SECONDS",
        DEFAULT_LLM_TIMEOUT_SECONDS,
        minimum=1,
    )


def llm_max_retries():
    return read_int_env(
        "ARGUS_LLM_MAX_RETRIES",
        DEFAULT_LLM_MAX_RETRIES,
        minimum=1,
    )


def llm_fallback_chat_urls():
    raw = first_env("ARGUS_LLM_FALLBACK_CHAT_URLS")
    if not raw:
        return []
    urls = []
    for item in raw.split(","):
        value = item.strip()
        if value:
            urls.append(value)
    return urls


def llm_fallback_api_bases():
    raw = first_env("ARGUS_LLM_FALLBACK_API_BASES")
    if not raw:
        return []
    bases = []
    for item in raw.split(","):
        value = item.strip()
        if value:
            bases.append(value)
    return bases


# ==========================================
# Logging
# ==========================================
def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log(worker, level, message):
    print(f"[{utc_now()}] [{worker}] [{level}] {message}")


# ==========================================
# Load task and contracts
# ==========================================
def load_task(task_dir):
    path = task_dir / "task.json"
    with open(path) as f:
        return json.load(f)


def load_soul(worker):
    path = AGENT_DIR / worker / "SOUL.md"
    if path.exists():
        with open(path) as f:
            return f.read()
    return f"You are {worker}."


def load_output_schema():
    if not OUTPUT_SCHEMA_PATH.exists():
        return {
            "required": ["task_id", "worker", "status", "summary", "artifacts", "timestamp"],
            "properties": {
                "task_id": {"type": "string", "pattern": "^[A-Z]+-[0-9]{8}-[0-9]{3}$"},
                "worker": {"type": "string", "enum": ["architect", "devops", "automation", "critic"]},
                "status": {"type": "string", "enum": ["success", "failed", "partial"]},
                "summary": {"type": "string"},
                "artifacts": {"type": "array"},
                "timestamp": {"type": "string"},
                "errors": {"type": "array"},
                "notes": {"type": "array"},
                "metadata": {"type": "object"},
                "duration_ms": {"type": "number"},
            },
            "$defs": {
                "artifact": {
                    "required": ["path", "type"],
                    "properties": {
                        "path": {"type": "string", "pattern": "^artifacts/"},
                        "type": {
                            "type": "string",
                            "enum": ["architecture", "script", "config", "review", "doc"],
                        },
                    },
                }
            },
        }
    with open(OUTPUT_SCHEMA_PATH) as f:
        return json.load(f)


def test_artifact_content(path, artifact_type, task, worker):
    task_id = task.get("task_id", "UNKNOWN")
    if artifact_type == "script":
        return (
            "#!/usr/bin/env python3\n"
            "import argparse\n\n"
            "def main() -> int:\n"
            "    parser = argparse.ArgumentParser()\n"
            "    parser.add_argument('--source', required=False)\n"
            "    parser.add_argument('--target', required=False)\n"
            "    parser.add_argument('--dry-run', action='store_true')\n"
            "    args = parser.parse_args()\n"
            "    print(f'Test script for {task_id}: dry_run={args.dry_run}')\n"
            "    return 0\n\n"
            "if __name__ == '__main__':\n"
            "    raise SystemExit(main())\n"
        )
    if artifact_type == "review":
        return (
            f"# Review ({task_id})\n\n"
            f"- Worker: {worker}\n"
            f"- Reviewed artifact target: {task.get('inputs', {})}\n"
            "- Verdict: pass (test mode)\n"
        )
    if artifact_type == "config":
        return "version: '3.9'\nservices:\n  app:\n    image: example\n"
    return f"# Test Artifact\n\nGenerated in test mode for `{task_id}` by `{worker}`.\nPath: `{path}`\n"


def build_test_mode_payload(task, worker, scenario):
    expected_outputs = task_expected_outputs(task)
    scenario_name = str(scenario or "success").strip().lower()

    if scenario_name == "failed":
        return {
            "status": "failed",
            "summary": f"Forced failed output for {task.get('task_id')} in test mode.",
            "errors": ["forced failure in test mode"],
            "metadata": {"test_mode": True, "scenario": scenario_name},
        }

    if scenario_name == "transient_failed":
        return {
            "status": "failed",
            "summary": f"Forced transient failed output for {task.get('task_id')} in test mode.",
            "errors": ["transient: simulated retryable failure"],
            "metadata": {"test_mode": True, "scenario": scenario_name},
        }

    if scenario_name == "partial":
        chosen = expected_outputs[:1]
        payload_status = "partial"
    else:
        chosen = expected_outputs
        payload_status = "success"

    file_contents = {}
    for artifact in chosen:
        file_contents[artifact["path"]] = test_artifact_content(
            artifact["path"],
            artifact["type"],
            task,
            worker,
        )

    return {
        "status": payload_status,
        "summary": f"Forced {payload_status} output for {task.get('task_id')} in test mode.",
        "file_contents": file_contents,
        "notes": [f"test mode scenario={scenario_name}"],
        "metadata": {"test_mode": True, "scenario": scenario_name},
    }


def load_test_mode_payload(task, worker):
    scenario = os.environ.get(TEST_SCENARIO_ENV)
    response_file = os.environ.get(TEST_RESPONSE_FILE_ENV)
    enabled = os.environ.get(TEST_MODE_ENV)

    if not enabled and not scenario and not response_file:
        return None

    mode_parts = []
    if enabled:
        mode_parts.append(f"{TEST_MODE_ENV}={enabled}")
    if scenario:
        mode_parts.append(f"{TEST_SCENARIO_ENV}={scenario}")
    if response_file:
        mode_parts.append(f"{TEST_RESPONSE_FILE_ENV}={response_file}")
    log(worker, "INFO", f"Test mode enabled ({', '.join(mode_parts)})")

    if response_file:
        response_path = Path(response_file)
        if not response_path.exists():
            raise RuntimeError(f"Test response file not found: {response_path}")
        with open(response_path) as f:
            payload = json.load(f)
        if not isinstance(payload, dict):
            raise RuntimeError("Test response file must contain a JSON object")
        return payload

    return build_test_mode_payload(task, worker, scenario or "success")


def llm_candidate_chat_urls(llm_settings):
    candidates = [llm_settings["chat_url"]]
    candidates.extend(llm_fallback_chat_urls())
    candidates.extend(normalize_chat_endpoint(base) for base in llm_fallback_api_bases())
    deduped = []
    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped


def classify_llm_call_error(error):
    status_code = None
    error_text = str(error or "")
    if isinstance(error, urllib.error.URLError) and getattr(error, "reason", None) is not None:
        error_text = f"{error_text} | reason={error.reason}"
    if isinstance(error, urllib.error.HTTPError):
        status_code = int(error.code)

    lowered = error_text.lower()
    if "unexpected_eof_while_reading" in lowered or "eof occurred in violation of protocol" in lowered:
        return "tls_eof", True
    if "timed out" in lowered:
        return "timeout", True
    if "name or service not known" in lowered or "name resolution" in lowered or "temporary failure in name resolution" in lowered:
        return "dns_resolution", True
    if "connection reset" in lowered:
        return "connection_reset", True
    if "connection refused" in lowered:
        return "connection_refused", True
    if "remote end closed connection" in lowered:
        return "remote_closed", True
    if status_code is not None:
        retryable_codes = {408, 409, 425, 429, 500, 502, 503, 504}
        return f"http_{status_code}", status_code in retryable_codes
    if isinstance(error, TimeoutError):
        return "timeout", True
    return "unknown", True


def should_retry_auth_failure_on_fallback(error_class, attempt, max_attempts, chat_urls):
    if error_class not in {"http_401", "http_403"}:
        return False
    if attempt >= max_attempts - 1:
        return False
    if len(chat_urls) < 2:
        return False
    current_url = chat_urls[attempt % len(chat_urls)]
    next_url = chat_urls[(attempt + 1) % len(chat_urls)]
    return current_url != next_url


def remove_endpoint_for_current_call(chat_urls, blocked_url):
    if len(chat_urls) <= 1:
        return chat_urls
    filtered = [url for url in chat_urls if url != blocked_url]
    if not filtered:
        return chat_urls
    return filtered


# ==========================================
# LLM Call with retry
# ==========================================
def call_llm(system_prompt, user_prompt, worker, llm_settings):
    timeout_seconds = llm_timeout_seconds()
    max_attempts = llm_max_retries()
    chat_urls = llm_candidate_chat_urls(llm_settings)
    payload = {
        "model": llm_settings["model_name"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {llm_settings['api_key']}",
        "User-Agent": HTTP_USER_AGENT,
        "Connection": "close",
    }
    auth_fallback_retry_used = False
    for attempt in range(max_attempts):
        chat_url = chat_urls[attempt % len(chat_urls)]
        try:
            req = urllib.request.Request(
                chat_url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with NO_PROXY_OPENER.open(req, timeout=timeout_seconds) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw)
            choices = result.get("choices", [])
            if not choices:
                raise RuntimeError("No choices returned")
            content = choices[0].get("message", {}).get("content", "")
            return content
        except Exception as e:
            error_class, retryable = classify_llm_call_error(e)
            auth_fallback_retry = False
            if not retryable and not auth_fallback_retry_used:
                auth_fallback_retry = should_retry_auth_failure_on_fallback(
                    error_class=error_class,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    chat_urls=chat_urls,
                )
                if auth_fallback_retry:
                    auth_fallback_retry_used = True
            effective_retryable = retryable or auth_fallback_retry
            log(
                worker,
                "WARN",
                (
                    f"LLM call failed attempt {attempt + 1}/{max_attempts} "
                    f"(endpoint={chat_url}, class={error_class}, retryable={effective_retryable}): {e}"
                ),
            )
            if attempt == max_attempts - 1 or not effective_retryable:
                raise RuntimeError(
                    (
                        f"LLM call exhausted (attempts={attempt + 1}/{max_attempts}, "
                        f"class={error_class}, endpoint={chat_url}, retryable={effective_retryable}): {e}"
                    )
                ) from e
            if auth_fallback_retry:
                log(worker, "INFO", "Authorization failure detected; retrying once on fallback endpoint.")
                next_chat_urls = remove_endpoint_for_current_call(chat_urls, chat_url)
                if next_chat_urls != chat_urls:
                    chat_urls = next_chat_urls
                    log(
                        worker,
                        "INFO",
                        f"Quarantined endpoint for current call due to authorization failure: {chat_url}",
                    )
            delay_seconds = 2 ** attempt
            next_url = chat_urls[(attempt + 1) % len(chat_urls)]
            log(worker, "INFO", f"Retrying LLM call in {delay_seconds}s (next_endpoint={next_url})")
            time.sleep(delay_seconds)
    return ""


# ==========================================
# Extract JSON from messy LLM output
# ==========================================
def extract_json(text):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass
    match = re.search(r"\{.*\}", text, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None


# ==========================================
# Task contract helpers
# ==========================================
def normalize_string_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_notes(value):
    return normalize_string_list(value)


def normalize_errors(value):
    return normalize_string_list(value)


def task_expected_outputs(task):
    outputs = task.get("expected_outputs")
    if not isinstance(outputs, list) or not outputs:
        raise RuntimeError("Task expected_outputs must be a non-empty list")
    normalized = []
    for item in outputs:
        if not isinstance(item, dict):
            raise RuntimeError("Task expected_outputs entries must be artifact objects")
        path = item.get("path")
        artifact_type = item.get("type")
        if not isinstance(path, str) or not path.startswith("artifacts/"):
            raise RuntimeError("Task expected_outputs.path must start with artifacts/")
        if not isinstance(artifact_type, str) or not artifact_type:
            raise RuntimeError("Task expected_outputs.type must be a non-empty string")
        normalized.append({"path": path, "type": artifact_type})
    return normalized


def infer_artifact_type(path):
    for prefix, artifact_type in ARTIFACT_TYPE_BY_PREFIX.items():
        if path.startswith(prefix):
            return artifact_type
    return DEFAULT_ARTIFACT_TYPE


def artifact_type_for_path(path, expected_type_map):
    return expected_type_map.get(path) or infer_artifact_type(path)


def validate_artifact_relative_path(path):
    if not isinstance(path, str) or not path.startswith("artifacts/"):
        raise RuntimeError(f"Artifact path must start with artifacts/: {path}")
    target_path = (BASE_DIR / path).resolve()
    artifacts_root = ARTIFACT_DIR.resolve()
    if not str(target_path).startswith(str(artifacts_root)):
        raise RuntimeError(f"Blocked path outside artifacts: {path}")
    return target_path


def write_artifacts(file_dict, expected_type_map, worker):
    written_artifacts = []
    if not isinstance(file_dict, dict):
        return written_artifacts
    for filepath, content in file_dict.items():
        try:
            if not isinstance(content, str):
                raise RuntimeError(f"Artifact content for {filepath} must be a string")
            if len(content.encode("utf-8")) > MAX_ARTIFACT_SIZE:
                raise RuntimeError(f"Artifact too large: {filepath}")
            target_path = validate_artifact_relative_path(filepath)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w") as f:
                f.write(content)
            artifact = {
                "path": filepath,
                "type": artifact_type_for_path(filepath, expected_type_map),
            }
            written_artifacts.append(artifact)
            log(worker, "INFO", f"Artifact written: {filepath}")
        except Exception as e:
            log(worker, "ERROR", f"Failed writing artifact {filepath}: {e}")
            raise
    return written_artifacts


def normalize_reported_artifacts(value, expected_type_map):
    artifacts = []
    if not value:
        return artifacts
    if not isinstance(value, list):
        raise RuntimeError("artifacts must be a list when returned by the model")
    for item in value:
        if isinstance(item, str):
            path = item
        elif isinstance(item, dict):
            path = item.get("path")
        else:
            raise RuntimeError("artifacts entries must be strings or objects")
        validate_artifact_relative_path(path)
        artifact_type = artifact_type_for_path(path, expected_type_map)
        artifacts.append({"path": path, "type": artifact_type})
    return artifacts


def dedupe_artifacts(artifacts):
    deduped = []
    seen = set()
    for artifact in artifacts:
        key = (artifact["path"], artifact["type"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(artifact)
    return deduped


def ensure_expected_match(artifacts, expected_outputs):
    expected_paths = {item["path"] for item in expected_outputs}
    actual_paths = {item["path"] for item in artifacts}
    return bool(expected_paths & actual_paths)


def ensure_valid_status(value):
    status = str(value or "success").strip().lower()
    if status not in ALLOWED_STATUSES:
        raise RuntimeError(f"Invalid status: {value}")
    return status


def ensure_timestamp(value):
    if not value:
        return utc_now()
    return str(value)


def validate_output_against_schema(payload, schema):
    errors = []
    required = schema.get("required", [])
    for field in required:
        if field not in payload:
            errors.append(f"Missing required field: {field}")

    allowed_keys = set(schema.get("properties", {}).keys())
    for key in payload.keys():
        if key not in allowed_keys:
            errors.append(f"Unexpected top-level field: {key}")

    properties = schema.get("properties", {})
    enum_status = properties.get("status", {}).get("enum", [])
    if payload.get("status") not in enum_status:
        errors.append("status is not allowed by schema")

    if not isinstance(payload.get("summary"), str) or not payload.get("summary", "").strip():
        errors.append("summary must be a non-empty string")

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str) or "T" not in timestamp:
        errors.append("timestamp must be an ISO datetime string")

    task_id_pattern = properties.get("task_id", {}).get("pattern")
    if task_id_pattern and not re.match(task_id_pattern, str(payload.get("task_id", ""))):
        errors.append("task_id does not match schema pattern")

    worker_enum = properties.get("worker", {}).get("enum", [])
    if payload.get("worker") not in worker_enum:
        errors.append("worker is not allowed by schema")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
    else:
        artifact_schema = schema.get("$defs", {}).get("artifact", {})
        required_artifact_fields = artifact_schema.get("required", [])
        allowed_artifact_types = set(
            artifact_schema.get("properties", {}).get("type", {}).get("enum", [])
        )
        path_pattern = artifact_schema.get("properties", {}).get("path", {}).get("pattern")
        for index, artifact in enumerate(artifacts):
            if not isinstance(artifact, dict):
                errors.append(f"artifacts[{index}] must be an object")
                continue
            for field in required_artifact_fields:
                if field not in artifact:
                    errors.append(f"artifacts[{index}] missing field: {field}")
            extra_artifact_keys = set(artifact.keys()) - set(artifact_schema.get("properties", {}).keys())
            for extra in sorted(extra_artifact_keys):
                errors.append(f"artifacts[{index}] unexpected field: {extra}")
            path = artifact.get("path", "")
            artifact_type = artifact.get("type")
            if not isinstance(path, str) or not re.match(path_pattern, path):
                errors.append(f"artifacts[{index}].path is invalid")
            if artifact_type not in allowed_artifact_types:
                errors.append(f"artifacts[{index}].type is invalid")

    if payload.get("status") in {"success", "partial"} and not artifacts:
        errors.append("success/partial output must include at least one artifact")

    for field in ("errors", "notes"):
        value = payload.get(field)
        if value is None:
            continue
        if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
            errors.append(f"{field} must be a list of non-empty strings")

    duration = payload.get("duration_ms")
    if duration is not None and (not isinstance(duration, (int, float)) or duration < 0):
        errors.append("duration_ms must be a non-negative number")

    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        errors.append("metadata must be an object")

    return errors


def build_failure_output(task_id, worker, summary, errors, started_at, metadata=None):
    duration_ms = int((time.monotonic() - started_at) * 1000)
    return {
        "task_id": task_id,
        "worker": worker,
        "status": "failed",
        "summary": summary,
        "artifacts": [],
        "errors": normalize_errors(errors),
        "metadata": metadata or {},
        "duration_ms": duration_ms,
        "timestamp": utc_now(),
    }


def finalize_output(task, worker, parsed, written_artifacts, started_at):
    expected_outputs = task_expected_outputs(task)
    expected_type_map = {item["path"]: item["type"] for item in expected_outputs}
    reported_artifacts = normalize_reported_artifacts(parsed.get("artifacts"), expected_type_map)
    artifacts = dedupe_artifacts(written_artifacts + reported_artifacts)
    status = ensure_valid_status(parsed.get("status", "success"))
    errors = normalize_errors(parsed.get("errors"))
    notes = normalize_notes(parsed.get("notes"))
    metadata = parsed.get("metadata") if isinstance(parsed.get("metadata"), dict) else {}
    summary = str(parsed.get("summary", "")).strip()

    if not summary:
        if artifacts:
            summary = f"Produced {len(artifacts)} artifact(s) for task {task['task_id']}."
        else:
            summary = f"Task {task['task_id']} finished without a usable summary."

    if status in {"success", "partial"}:
        if not artifacts:
            raise RuntimeError("success/partial output requires at least one artifact")
        if not ensure_expected_match(artifacts, expected_outputs):
            raise RuntimeError("No produced artifact matched task.expected_outputs")
    else:
        artifacts = []
        if not errors:
            errors = ["Worker reported failed without structured errors"]

    final_output = {
        "task_id": task["task_id"],
        "worker": worker,
        "status": status,
        "summary": summary,
        "artifacts": artifacts,
        "timestamp": utc_now(),
        "duration_ms": int((time.monotonic() - started_at) * 1000),
    }
    if errors:
        final_output["errors"] = errors
    if notes:
        final_output["notes"] = notes
    if metadata:
        final_output["metadata"] = metadata
    return final_output


def ensure_output_is_schema_valid(output_payload, schema, started_at):
    validation_errors = validate_output_against_schema(output_payload, schema)
    if not validation_errors:
        return output_payload
    fallback = build_failure_output(
        output_payload.get("task_id", "UNKNOWN"),
        output_payload.get("worker", "unknown"),
        "Schema validation failed for output.json",
        ["schema validation failed", *validation_errors],
        started_at,
        metadata={"invalid_output": output_payload},
    )
    second_pass_errors = validate_output_against_schema(fallback, schema)
    if second_pass_errors:
        fallback["errors"] = fallback.get("errors", []) + second_pass_errors
    return fallback


def build_user_prompt(task):
    return f"""
Task ID: {task.get('task_id', '')}
Worker: {task.get('worker', '')}
Task Type: {task.get('task_type', '')}
Objective: {task.get('objective', '')}
Inputs: {json.dumps(task.get('inputs', {}), ensure_ascii=False)}
Constraints: {json.dumps(task.get('constraints', []), ensure_ascii=False)}
Expected Outputs: {json.dumps(task.get('expected_outputs', []), ensure_ascii=False)}
Acceptance Criteria: {json.dumps(task.get('acceptance_criteria', []), ensure_ascii=False)}
Source: {json.dumps(task.get('source', {}), ensure_ascii=False)}
Metadata: {json.dumps(task.get('metadata', {}), ensure_ascii=False)}

CRITICAL CONTRACT INSTRUCTION:
Return a single valid JSON object.
Allowed top-level fields from the model response:
- status
- summary
- artifacts
- errors
- notes
- metadata
- file_contents

Rules:
- status must be one of success, failed, partial
- file_contents keys must be relative artifact paths under artifacts/
- align created files with expected_outputs whenever possible
- do not invent artifacts that were not actually created
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", required=True)
    parser.add_argument("--worker")
    return parser.parse_args()


def run_worker(task_dir=None, worker_override=None, base_dir=None, llm_override=None):
    if task_dir is None:
        args = parse_args()
        task_dir = args.task_dir
        if worker_override is None:
            worker_override = args.worker

    configure_paths(base_dir=base_dir)
    started_at = time.monotonic()
    task_dir = Path(task_dir)
    task_dir.mkdir(parents=True, exist_ok=True)
    task_id = task_dir.name
    worker = worker_override or os.environ.get("WORKER_NAME", "unknown")
    output_path = task_dir / "output.json"

    try:
        task = load_task(task_dir)
        task_id = task.get("task_id", task_id)
        worker = task.get("worker", worker)
        schema = load_output_schema()
        expected_outputs = task_expected_outputs(task)
        expected_type_map = {item["path"]: item["type"] for item in expected_outputs}

        llm_settings = None
        parsed = load_test_mode_payload(task, worker)
        if parsed is None:
            if llm_override is not None:
                parsed = llm_override(task=task, worker=worker)
            else:
                llm_settings = get_llm_settings()
                log(
                    worker,
                    "INFO",
                    "Worker started using endpoint "
                    f"{llm_settings['chat_url']} "
                    f"(timeout={llm_timeout_seconds()}s, attempts={llm_max_retries()})",
                )
                soul = load_soul(worker)
                user_prompt = build_user_prompt(task)
                llm_output = call_llm(soul, user_prompt, worker, llm_settings)
                parsed = extract_json(llm_output)
                if parsed is None:
                    raise RuntimeError("LLM output not valid JSON")
                if not isinstance(parsed, dict):
                    raise RuntimeError("LLM output must be a JSON object")
        elif not isinstance(parsed, dict):
            raise RuntimeError("Test mode payload must be a JSON object")

        written_artifacts = []
        if "file_contents" in parsed:
            written_artifacts = write_artifacts(parsed["file_contents"], expected_type_map, worker)

        final_output = finalize_output(task, worker, parsed, written_artifacts, started_at)
        final_output = ensure_output_is_schema_valid(final_output, schema, started_at)
        log(worker, "INFO", f"Task completed {task_id} with status {final_output['status']}")
    except Exception as e:
        log(worker, "ERROR", f"Task failed {task_id}: {e}")
        schema = load_output_schema()
        final_output = build_failure_output(
            task_id,
            worker,
            "Worker execution failed",
            [str(e)],
            started_at,
        )
        final_output = ensure_output_is_schema_valid(final_output, schema, started_at)

    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)
    log(worker, "INFO", f"Worker exiting from {task_dir}")


if __name__ == "__main__":
    run_worker()
