from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from argus_contracts import validate_task
from skills.delegate_task import delegate_task


PREVIEW_DIR = REPO_ROOT / "preview"
APPROVALS_DIR = REPO_ROOT / "approvals"
VERDICT_VALUES = {"pass", "fail", "needs_revision"}
DEFAULT_MAX_SNAPSHOT_CHARS = 120000
MIN_MAX_SNAPSHOT_CHARS = 4096
MAX_ALLOWED_SNAPSHOT_CHARS = 500000
TRANSIENT_AUTOMATION_ERROR_CLASSES = {"http_524", "http_502", "timeout"}
DEFAULT_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS = 1
MAX_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS = 3
DEFAULT_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS = 1
MAX_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS = 2
WORKSPACE_PRESENCE_FAILURE_SNIPPETS = (
    "repository not present in execution environment",
    "workspace directory was empty",
    "lacks an accessible repository layout",
    "did not provide repository access",
)


def _resolve_max_snapshot_chars() -> int:
    raw = os.environ.get("ARGUS_CRITIC_MAX_SNAPSHOT_CHARS", "").strip()
    if not raw:
        return DEFAULT_MAX_SNAPSHOT_CHARS
    try:
        parsed = int(raw)
    except Exception:
        return DEFAULT_MAX_SNAPSHOT_CHARS
    return max(MIN_MAX_SNAPSHOT_CHARS, min(parsed, MAX_ALLOWED_SNAPSHOT_CHARS))


MAX_SNAPSHOT_CHARS = _resolve_max_snapshot_chars()


def _resolve_automation_transient_retry_attempts() -> int:
    raw = os.environ.get("ARGUS_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS", "").strip()
    if not raw:
        return DEFAULT_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS
    try:
        parsed = int(raw)
    except Exception:
        return DEFAULT_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS
    return max(0, min(parsed, MAX_AUTOMATION_TRANSIENT_RETRY_ATTEMPTS))


def _resolve_automation_workspace_retry_attempts() -> int:
    raw = os.environ.get("ARGUS_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS", "").strip()
    if not raw:
        return DEFAULT_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS
    try:
        parsed = int(raw)
    except Exception:
        return DEFAULT_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS
    return max(0, min(parsed, MAX_AUTOMATION_WORKSPACE_RETRY_ATTEMPTS))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    APPROVALS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute approved preview tasks only; unapproved previews are never dispatched."
    )
    parser.add_argument("--once", action="store_true", help="Process approvals once and exit.")
    parser.add_argument("--preview-id", default=None, help="Run only a specific preview id.")
    parser.add_argument(
        "--test-mode",
        choices=("off", "success", "partial", "failed", "transient_failed"),
        default="success",
        help="Worker test mode routed through delegate_task; use off for real LLM execution.",
    )
    parser.add_argument(
        "--allow-replay",
        action="store_true",
        help="Explicitly allow re-running a preview that has already been executed.",
    )
    return parser.parse_args()


def _normalize_review_line(line: str) -> str:
    normalized = line.strip()
    normalized = re.sub(r"^[-*+]\s*", "", normalized)
    normalized = normalized.replace("**", "").replace("__", "")
    return normalized.strip()


def _extract_verdict_from_review_text(text: str) -> str | None:
    explicit_matches: list[str] = []
    lines = text.splitlines()
    for raw_line in lines:
        normalized = _normalize_review_line(raw_line)
        match = re.match(r"^verdict\s*[:=]\s*(pass|fail|needs_revision)\b", normalized, re.I)
        if match:
            explicit_matches.append(match.group(1).lower())
    if explicit_matches:
        # Prefer the final explicit verdict line from the rendered review, not
        # earlier prompt/contract fragments embedded in the artifact body.
        return explicit_matches[-1]

    for idx, raw_line in enumerate(lines):
        normalized = _normalize_review_line(raw_line)
        if not re.match(r"^(?:#+\s*)?verdict\b", normalized, re.I):
            continue
        for candidate in lines[idx + 1 :]:
            candidate_normalized = _normalize_review_line(candidate)
            if not candidate_normalized:
                continue
            match = re.match(r"^(pass|fail|needs_revision)\b", candidate_normalized, re.I)
            if match:
                return match.group(1).lower()
            break

    return None


def extract_critic_verdict(critic_result: dict[str, Any], review_artifact_path: str | None) -> str:
    metadata = critic_result.get("metadata")
    if isinstance(metadata, dict):
        for key in ("verdict", "review_verdict"):
            verdict = metadata.get(key)
            if isinstance(verdict, str):
                norm = verdict.strip().lower()
                if norm in VERDICT_VALUES:
                    return norm

    summary = critic_result.get("summary")
    if isinstance(summary, str):
        match = re.search(r"\b(pass|fail|needs_revision)\b", summary.lower())
        if match:
            return match.group(1)

    if review_artifact_path:
        review_path = (REPO_ROOT / review_artifact_path).resolve()
        if review_path.exists():
            text = review_path.read_text(encoding="utf-8", errors="ignore")
            review_verdict = _extract_verdict_from_review_text(text)
            if review_verdict:
                return review_verdict

    status = str(critic_result.get("status", "")).strip().lower()
    if status == "failed":
        return "fail"
    return "needs_revision"


def _read_artifact_text(relative_path: str) -> dict[str, Any]:
    if not isinstance(relative_path, str) or not relative_path.startswith("artifacts/"):
        return {
            "path": relative_path,
            "available": False,
            "error": "invalid_artifact_path",
        }
    target = (REPO_ROOT / relative_path).resolve()
    artifacts_root = (REPO_ROOT / "artifacts").resolve()
    if not str(target).startswith(str(artifacts_root)):
        return {
            "path": relative_path,
            "available": False,
            "error": "artifact_path_outside_artifacts",
        }
    if not target.exists():
        return {
            "path": relative_path,
            "available": False,
            "error": "artifact_not_found",
        }
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {
            "path": relative_path,
            "available": False,
            "error": f"artifact_read_failed:{exc}",
        }
    was_truncated = len(text) > MAX_SNAPSHOT_CHARS
    if was_truncated:
        text = text[:MAX_SNAPSHOT_CHARS]
    return {
        "path": relative_path,
        "available": True,
        "content": text,
        "truncated": was_truncated,
    }


def _critic_review_contract(expected_review_path: str) -> dict[str, Any]:
    return {
        "required_status": ["success", "partial", "failed"],
        "required_verdict_values": sorted(VERDICT_VALUES),
        "required_metadata_key": "verdict",
        "must_write_review_artifact_to": expected_review_path,
        "artifact_policy": (
            "Always include either `file_contents` for the review artifact path or "
            "`artifacts` referencing that exact path."
        ),
        "fallback_policy": (
            "If evidence is insufficient, return `status=partial`, include explicit `errors`, "
            "still generate review artifact content, and set verdict=needs_revision."
        ),
    }


def _append_normalized_artifact(
    normalized_artifacts: list[dict[str, Any]],
    seen_paths: set[str],
    item: Any,
) -> None:
    if isinstance(item, dict):
        path = item.get("path")
        atype = item.get("type")
        if not isinstance(path, str) or path in seen_paths:
            return
        normalized_artifacts.append(
            {
                "path": path,
                "type": atype if isinstance(atype, str) else "doc",
            }
        )
        seen_paths.add(path)
        return
    if isinstance(item, str) and item not in seen_paths:
        normalized_artifacts.append({"path": item, "type": "doc"})
        seen_paths.add(item)


def build_critic_from_automation(critic_task: dict[str, Any], auto_result: dict[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(critic_task))
    artifacts = auto_result.get("artifacts")
    updated.setdefault("inputs", {})
    updated.setdefault("constraints", [])

    normalized_artifacts: list[dict[str, Any]] = []
    snapshots: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    existing_artifacts = updated["inputs"].get("artifacts")
    if isinstance(existing_artifacts, list):
        for item in existing_artifacts:
            _append_normalized_artifact(normalized_artifacts, seen_paths, item)
    if isinstance(artifacts, list):
        for item in artifacts:
            _append_normalized_artifact(normalized_artifacts, seen_paths, item)
    for artifact in normalized_artifacts:
        snapshots.append(_read_artifact_text(artifact["path"]))
    if normalized_artifacts:
        updated["inputs"]["artifacts"] = normalized_artifacts

    params = updated["inputs"].get("params")
    if not isinstance(params, dict):
        params = {}
    params["artifact_snapshots"] = snapshots

    expected_outputs = updated.get("expected_outputs")
    expected_review_path = "artifacts/reviews/pdf_to_excel_ocr_inbox_review.md"
    if isinstance(expected_outputs, list):
        for item in expected_outputs:
            if isinstance(item, dict):
                path = item.get("path")
                if isinstance(path, str) and path.startswith("artifacts/"):
                    expected_review_path = path
                    break

    params["review_contract"] = _critic_review_contract(expected_review_path)
    params["review_template"] = {
        "title": "Review: <artifact name>",
        "sections": ["Scope", "Findings", "Verdict", "Rationale"],
        "verdict_required": True,
    }
    updated["inputs"]["params"] = params

    # Tighten critic behavior with explicit deterministic contract reminders.
    constraints = updated["constraints"]
    if not isinstance(constraints, list):
        constraints = []
    constraints.extend(
        [
            "Use artifact_snapshots when provided; avoid claiming access problems if snapshot content exists.",
            "When both the generated wrapper and reviewed delegate snapshots are provided, review them together rather than silently narrowing scope to one file.",
            "Return metadata.verdict with one of: pass, fail, needs_revision.",
            "Always generate review artifact content for expected_outputs[0].path.",
            "If evidence is insufficient, use partial + errors + verdict=needs_revision, but still output review artifact.",
        ]
    )
    updated["constraints"] = constraints
    return updated


def decision_for_results(auto_result: dict[str, Any], critic_result: dict[str, Any], verdict: str) -> tuple[str, str]:
    auto_status = str(auto_result.get("status", "")).strip().lower()
    critic_status = str(critic_result.get("status", "")).strip().lower()
    if auto_status not in {"success", "partial"}:
        return "rejected", f"automation_status={auto_status}"
    if critic_status not in {"success", "partial"}:
        return "rejected", f"critic_status={critic_status}"
    if verdict == "pass":
        return "processed", "critic_verdict=pass"
    return "rejected", f"critic_verdict={verdict}"


def _extract_llm_error_class(auto_result: dict[str, Any]) -> str | None:
    errors = auto_result.get("errors")
    if not isinstance(errors, list):
        return None
    for item in errors:
        if not isinstance(item, str):
            continue
        match = re.search(r"class=([a-z0-9_]+)", item)
        if match:
            return match.group(1).strip().lower()
    return None


def _can_retry_automation_after_transient_failure(
    auto_result: dict[str, Any],
    *,
    retries_used: int,
    retry_budget: int,
) -> bool:
    if retries_used >= retry_budget:
        return False
    if str(auto_result.get("status", "")).strip().lower() in {"success", "partial"}:
        return False
    error_class = _extract_llm_error_class(auto_result)
    return bool(error_class and error_class in TRANSIENT_AUTOMATION_ERROR_CLASSES)


def _is_workspace_presence_failure(auto_result: dict[str, Any]) -> bool:
    if str(auto_result.get("status", "")).strip().lower() in {"success", "partial"}:
        return False
    chunks: list[str] = []
    summary = auto_result.get("summary")
    if isinstance(summary, str):
        chunks.append(summary)
    errors = auto_result.get("errors")
    if isinstance(errors, list):
        chunks.extend(item for item in errors if isinstance(item, str))
    if not chunks:
        return False
    blob = "\n".join(chunks).lower()
    if any(snippet in blob for snippet in WORKSPACE_PRESENCE_FAILURE_SNIPPETS):
        return True
    repo_signal = "repository" in blob
    workspace_signal = ("workspace" in blob) or ("/app/workspaces" in blob) or ("task.json" in blob)
    missing_signal = ("did not provide" in blob) or ("missing" in blob) or ("empty" in blob) or ("no " in blob)
    return bool(repo_signal and workspace_signal and missing_signal)


def _can_retry_automation_after_workspace_presence_failure(
    auto_result: dict[str, Any],
    *,
    retries_used: int,
    retry_budget: int,
) -> bool:
    if retries_used >= retry_budget:
        return False
    return _is_workspace_presence_failure(auto_result)


def load_approvals(preview_id: str | None) -> list[tuple[Path, dict[str, Any]]]:
    approvals = []
    if preview_id:
        paths = [APPROVALS_DIR / f"{preview_id}.json"]
    else:
        paths = sorted(APPROVALS_DIR.glob("*.json"))
    for path in paths:
        if not path.exists():
            continue
        payload = load_json(path)
        approvals.append((path, payload))
    return approvals


def update_preview_execution(
    *,
    preview_path: Path,
    preview_payload: dict[str, Any],
    decision: str,
    decision_reason: str,
    approval_path: Path,
    approval_payload: dict[str, Any],
    auto_result: dict[str, Any] | None,
    critic_result: dict[str, Any] | None,
    critic_verdict: str,
) -> None:
    execution = preview_payload.get("execution")
    if not isinstance(execution, dict):
        execution = {}
    attempts_raw = execution.get("attempts", 0)
    attempts = int(attempts_raw) if isinstance(attempts_raw, int) or str(attempts_raw).isdigit() else 0
    execution.update(
        {
            "status": decision,
            "executed": True,
            "executed_at": utc_now(),
            "attempts": attempts + 1,
            "decision_reason": decision_reason,
        }
    )
    preview_payload["execution"] = execution
    preview_payload["approved"] = bool(approval_payload.get("approved", False))
    preview_payload["approval"] = {
        "approval_file": str(approval_path),
        "approved_by": approval_payload.get("approved_by"),
        "approved_at": approval_payload.get("approved_at"),
        "note": approval_payload.get("note"),
    }
    preview_payload["last_execution"] = {
        "decision": decision,
        "decision_reason": decision_reason,
        "automation_result": auto_result,
        "critic_result": critic_result,
        "critic_verdict": critic_verdict,
    }
    write_json(preview_path, preview_payload)


def process_approval(approval_path: Path, approval: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    preview_id = str(approval.get("preview_id") or "").strip()
    if not preview_id:
        return {
            "status": "rejected",
            "decision_reason": "approval_missing_preview_id",
            "approval_file": str(approval_path),
        }
    if not bool(approval.get("approved", False)):
        return {
            "status": "skipped",
            "decision_reason": "approval_flag_not_true",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    preview_path = PREVIEW_DIR / f"{preview_id}.json"
    if not preview_path.exists():
        return {
            "status": "rejected",
            "decision_reason": "preview_not_found",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    preview_payload = load_json(preview_path)
    execution = preview_payload.get("execution", {})
    execution_status = str(execution.get("status", "")).strip().lower() if isinstance(execution, dict) else ""
    if execution_status in {"processed", "rejected"} and not args.allow_replay:
        return {
            "status": "skipped",
            "decision_reason": "already_executed_use_allow_replay",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    tasks = preview_payload.get("internal_tasks")
    if not isinstance(tasks, dict):
        return {
            "status": "rejected",
            "decision_reason": "preview_missing_internal_tasks",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
        }

    auto_task = tasks.get("automation")
    critic_task = tasks.get("critic")
    auto_errors = validate_task(auto_task)
    critic_errors = validate_task(critic_task)
    if auto_errors or critic_errors:
        return {
            "status": "rejected",
            "decision_reason": "preview_task_validate_failed",
            "preview_id": preview_id,
            "approval_file": str(approval_path),
            "automation_errors": auto_errors,
            "critic_errors": critic_errors,
        }

    auto_result: dict[str, Any] | None = None
    critic_result: dict[str, Any] | None = None
    verdict = "needs_revision"
    decision = "rejected"
    decision_reason = "execution_failed"
    auto_transient_retries_used = 0
    auto_workspace_retries_used = 0

    try:
        dt_kwargs = {
            "timeout": 600,
            "retry_attempts": 0,
        }
        if args.test_mode != "off":
            dt_kwargs["test_mode"] = args.test_mode

        retry_budget = _resolve_automation_transient_retry_attempts()
        workspace_retry_budget = _resolve_automation_workspace_retry_attempts()
        while True:
            auto_result = delegate_task("automation", auto_task, **dt_kwargs)
            if auto_result.get("status") in {"success", "partial"}:
                break
            if _can_retry_automation_after_transient_failure(
                auto_result,
                retries_used=auto_transient_retries_used,
                retry_budget=retry_budget,
            ):
                auto_transient_retries_used += 1
                continue
            if _can_retry_automation_after_workspace_presence_failure(
                auto_result,
                retries_used=auto_workspace_retries_used,
                retry_budget=workspace_retry_budget,
            ):
                auto_workspace_retries_used += 1
                continue
            raise RuntimeError(f"Automation task failed: {json.dumps(auto_result, ensure_ascii=False)}")

        if auto_transient_retries_used > 0 or auto_workspace_retries_used > 0:
            metadata = auto_result.get("metadata")
            if not isinstance(metadata, dict):
                metadata = {}
            if auto_transient_retries_used > 0:
                metadata["automation_transient_retries_used"] = auto_transient_retries_used
            if auto_workspace_retries_used > 0:
                metadata["automation_workspace_retries_used"] = auto_workspace_retries_used
            auto_result["metadata"] = metadata

        critic_task = build_critic_from_automation(critic_task, auto_result)
        critic_post_errors = validate_task(critic_task)
        if critic_post_errors:
            raise RuntimeError(
                "Critic task invalid after automation mapping: "
                + json.dumps(critic_post_errors, ensure_ascii=False)
            )

        critic_result = delegate_task("critic", critic_task, **dt_kwargs)
        if critic_result.get("status") not in {"success", "partial"}:
            raise RuntimeError(f"Critic task failed: {json.dumps(critic_result, ensure_ascii=False)}")

        review_artifact_path = None
        artifacts = critic_result.get("artifacts")
        if isinstance(artifacts, list) and artifacts:
            first = artifacts[0]
            if isinstance(first, dict):
                review_artifact_path = first.get("path")
            elif isinstance(first, str):
                review_artifact_path = first
        verdict = extract_critic_verdict(critic_result, review_artifact_path)
        decision, decision_reason = decision_for_results(auto_result, critic_result, verdict)
    except Exception as exc:
        decision = "rejected"
        decision_reason = str(exc)

    update_preview_execution(
        preview_path=preview_path,
        preview_payload=preview_payload,
        decision=decision,
        decision_reason=decision_reason,
        approval_path=approval_path,
        approval_payload=approval,
        auto_result=auto_result,
        critic_result=critic_result,
        critic_verdict=verdict,
    )

    sidecar = {
        "preview_id": preview_id,
        "approval_file": str(approval_path),
        "executed_at": utc_now(),
        "status": decision,
        "decision_reason": decision_reason,
        "critic_verdict": verdict,
        "automation_transient_retries_used": auto_transient_retries_used,
        "automation_workspace_retries_used": auto_workspace_retries_used,
        "test_mode": args.test_mode,
    }
    sidecar_path = APPROVALS_DIR / f"{preview_id}.result.json"
    write_json(sidecar_path, sidecar)

    return {
        "status": decision,
        "decision_reason": decision_reason,
        "preview_id": preview_id,
        "approval_file": str(approval_path),
        "result_sidecar": str(sidecar_path),
        "critic_verdict": verdict,
        "automation_transient_retries_used": auto_transient_retries_used,
        "automation_workspace_retries_used": auto_workspace_retries_used,
    }


def main() -> int:
    args = parse_args()
    ensure_dirs()

    approvals = load_approvals(args.preview_id)
    if not approvals:
        print(json.dumps({"status": "idle", "message": "No approval files found."}, ensure_ascii=False))
        return 0

    results = []
    for approval_path, approval in approvals:
        results.append(process_approval(approval_path, approval, args))

    payload = {
        "status": "done",
        "processed": len([r for r in results if r["status"] == "processed"]),
        "rejected": len([r for r in results if r["status"] == "rejected"]),
        "skipped": len([r for r in results if r["status"] == "skipped"]),
        "test_mode": args.test_mode,
        "allow_replay": args.allow_replay,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ARGUS_BASE_DIR", str(REPO_ROOT))
    os.environ.setdefault("ARGUS_APP_HOST_PATH", str(REPO_ROOT))
    raise SystemExit(main())
