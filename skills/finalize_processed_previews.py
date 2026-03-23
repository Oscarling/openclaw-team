from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PREVIEW_DIR = REPO_ROOT / "preview"
APPROVALS_DIR = REPO_ROOT / "approvals"
PROCESSED_DIR = REPO_ROOT / "processed"
TASKS_DIR = REPO_ROOT / "tasks"
WORKSPACES_DIR = REPO_ROOT / "workspaces"

DONE_LIST_NAME_CANDIDATES = ("done", "完成", "completed", "complete")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
        description=(
            "Finalize already-processed previews via git commit/push and Trello Done move. "
            "Does not rerun automation/critic."
        )
    )
    parser.add_argument("--once", action="store_true", help="Process current previews once and exit.")
    parser.add_argument("--preview-id", default=None, help="Finalize only a specific preview id.")
    parser.add_argument(
        "--git-remote",
        default=os.environ.get("GIT_PUSH_REMOTE"),
        help="Git push destination. Accepts a configured remote name or a direct URL/path.",
    )
    parser.add_argument(
        "--git-branch",
        default=os.environ.get("GIT_PUSH_BRANCH"),
        help="Destination branch for git push. Defaults to the current branch.",
    )
    parser.add_argument(
        "--trello-done-list-id",
        default=os.environ.get("TRELLO_DONE_LIST_ID"),
        help="Explicit Trello Done list id. If omitted, the helper tries env name override then common Done names.",
    )
    parser.add_argument(
        "--trello-done-list-name",
        default=os.environ.get("TRELLO_DONE_LIST_NAME"),
        help="Explicit Trello Done list name fallback when list id is not provided.",
    )
    parser.add_argument(
        "--allow-replay-finalization",
        action="store_true",
        help="Allow rerunning finalization even after it was already completed.",
    )
    return parser.parse_args()


def _pick_env(primary: str, alias: str) -> tuple[str | None, str]:
    primary_val = os.environ.get(primary)
    if primary_val:
        return primary_val, primary
    alias_val = os.environ.get(alias)
    if alias_val:
        return alias_val, alias
    return None, "missing"


def _trello_auth() -> dict[str, Any]:
    api_key, key_source = _pick_env("TRELLO_API_KEY", "TRELLO_KEY")
    api_token, token_source = _pick_env("TRELLO_API_TOKEN", "TRELLO_TOKEN")
    return {
        "api_key": api_key,
        "api_token": api_token,
        "selected_names": {"key": key_source, "token": token_source},
        "presence": {
            "TRELLO_API_KEY": "set" if os.environ.get("TRELLO_API_KEY") else "missing",
            "TRELLO_KEY": "set" if os.environ.get("TRELLO_KEY") else "missing",
            "TRELLO_API_TOKEN": "set" if os.environ.get("TRELLO_API_TOKEN") else "missing",
            "TRELLO_TOKEN": "set" if os.environ.get("TRELLO_TOKEN") else "missing",
            "TRELLO_BOARD_ID": "set" if os.environ.get("TRELLO_BOARD_ID") else "missing",
            "TRELLO_LIST_ID": "set" if os.environ.get("TRELLO_LIST_ID") else "missing",
        },
    }


def _normalize_list_name(name: str) -> str:
    return "".join(str(name or "").strip().lower().split())


def _git_current_branch(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    branch = proc.stdout.strip()
    if not branch:
        raise RuntimeError("Unable to determine current git branch")
    return branch


def _git_origin_url(repo_root: Path) -> str | None:
    proc = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    url = proc.stdout.strip()
    return url or None


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )


def _relative(path: Path, repo_root: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def _existing_relative_paths(paths: list[Path], repo_root: Path) -> list[str]:
    rels: list[str] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.resolve()
            resolved.relative_to(repo_root.resolve())
        except Exception:
            continue
        if not resolved.exists() or not resolved.is_file():
            continue
        rel = _relative(resolved, repo_root)
        if rel in seen:
            continue
        seen.add(rel)
        rels.append(rel)
    return rels


def _collect_commit_paths(preview_path: Path, preview_payload: dict[str, Any], repo_root: Path) -> list[str]:
    approvals_dir = repo_root / "approvals"
    processed_dir = repo_root / "processed"
    tasks_dir = repo_root / "tasks"
    workspaces_dir = repo_root / "workspaces"
    paths: list[Path] = []

    approval = preview_payload.get("approval")
    if isinstance(approval, dict):
        approval_file = approval.get("approval_file")
        if isinstance(approval_file, str):
            approval_path = Path(approval_file)
            paths.append(approval_path)
            paths.append(approvals_dir / f"{preview_payload['preview_id']}.result.json")

    source = preview_payload.get("source")
    if isinstance(source, dict):
        inbox_file = source.get("inbox_file")
        if isinstance(inbox_file, str) and inbox_file.strip():
            processed_path = processed_dir / inbox_file
            paths.append(processed_path)
            paths.append(processed_path.with_name(processed_path.name + ".result.json"))

    last_execution = preview_payload.get("last_execution")
    if isinstance(last_execution, dict):
        for result_key in ("automation_result", "critic_result"):
            result = last_execution.get(result_key)
            if not isinstance(result, dict):
                continue
            task_id = result.get("task_id")
            worker = result.get("worker")
            if isinstance(task_id, str) and task_id.strip():
                paths.append(tasks_dir / f"{task_id}.json")
                if isinstance(worker, str) and worker.strip():
                    workspace_dir = workspaces_dir / worker / task_id
                    if workspace_dir.exists():
                        paths.extend(sorted(p for p in workspace_dir.rglob("*") if p.is_file()))
            artifacts = result.get("artifacts")
            if isinstance(artifacts, list):
                for artifact in artifacts:
                    if isinstance(artifact, dict):
                        rel = artifact.get("path")
                    else:
                        rel = artifact
                    if isinstance(rel, str) and rel.startswith("artifacts/"):
                        paths.append(repo_root / rel)

    return _existing_relative_paths(paths, repo_root)


def _load_finalization_state(preview_payload: dict[str, Any]) -> dict[str, Any]:
    existing = preview_payload.get("finalization")
    if isinstance(existing, dict):
        return json.loads(json.dumps(existing))
    return {
        "status": "pending",
        "attempts": 0,
        "git": {
            "add": {"status": "pending"},
            "commit": {"status": "pending"},
            "push": {"status": "pending"},
        },
        "trello": {"status": "pending"},
    }


def _persist_finalization(
    preview_path: Path,
    preview_payload: dict[str, Any],
    finalization: dict[str, Any],
    *,
    repo_root: Path,
) -> Path:
    approvals_dir = repo_root / "approvals"
    preview_payload["finalization"] = finalization
    write_json(preview_path, preview_payload)
    sidecar = approvals_dir / f"{preview_payload['preview_id']}.finalization.result.json"
    write_json(
        sidecar,
        {
            "preview_id": preview_payload["preview_id"],
            "updated_at": utc_now(),
            "finalization": finalization,
        },
    )
    return sidecar


def _resolve_done_list_id(
    *,
    board_id: str,
    done_list_id: str | None,
    done_list_name: str | None,
    requests_get: Callable[..., Any],
) -> tuple[str, dict[str, Any]]:
    if done_list_id:
        return done_list_id, {"resolution": "explicit_list_id", "done_list_id": done_list_id}

    auth = _trello_auth()
    api_key = auth["api_key"]
    api_token = auth["api_token"]
    if not api_key or not api_token:
        raise RuntimeError("Missing Trello write credentials")

    response = requests_get(
        f"https://api.trello.com/1/boards/{board_id}/lists",
        params={
            "key": api_key,
            "token": api_token,
            "fields": "id,name,closed,pos",
        },
        timeout=20,
    )
    if response.status_code != 200:
        body = (response.text or "")[:300]
        raise RuntimeError(f"Unable to resolve Trello Done list: HTTP {response.status_code}; response_preview={body}")

    lists = response.json()
    if not isinstance(lists, list):
        raise RuntimeError("Unexpected Trello list response shape")

    target_names = []
    if done_list_name:
        target_names.append(_normalize_list_name(done_list_name))
    target_names.extend(_normalize_list_name(name) for name in DONE_LIST_NAME_CANDIDATES)
    target_names = [name for i, name in enumerate(target_names) if name and name not in target_names[:i]]

    for candidate in lists:
        if not isinstance(candidate, dict) or candidate.get("closed"):
            continue
        current_name = _normalize_list_name(str(candidate.get("name") or ""))
        if current_name in target_names:
            return str(candidate.get("id") or "").strip(), {
                "resolution": "board_list_lookup",
                "done_list_id": str(candidate.get("id") or "").strip(),
                "done_list_name": candidate.get("name"),
            }

    raise RuntimeError("Unable to resolve Trello Done list from board lists")


def process_preview(
    preview_path: Path,
    *,
    repo_root: Path,
    git_remote: str | None,
    git_branch: str | None,
    trello_done_list_id: str | None,
    trello_done_list_name: str | None,
    allow_replay_finalization: bool,
    requests_get: Callable[..., Any] = requests.get,
    requests_put: Callable[..., Any] = requests.put,
) -> dict[str, Any]:
    preview_payload = load_json(preview_path)
    preview_id = str(preview_payload.get("preview_id") or preview_path.stem).strip()
    execution = preview_payload.get("execution")
    if not isinstance(execution, dict):
        return {
            "status": "skipped",
            "decision_reason": "preview_missing_execution_state",
            "preview_id": preview_id,
        }

    execution_status = str(execution.get("status") or "").strip().lower()
    if execution_status != "processed":
        return {
            "status": "skipped",
            "decision_reason": f"execution_status_not_processed:{execution_status or 'missing'}",
            "preview_id": preview_id,
        }
    if not bool(execution.get("executed", False)):
        return {
            "status": "skipped",
            "decision_reason": "preview_not_executed",
            "preview_id": preview_id,
        }

    finalization = _load_finalization_state(preview_payload)
    if finalization.get("status") == "completed" and not allow_replay_finalization:
        return {
            "status": "skipped",
            "decision_reason": "already_finalized_use_allow_replay_finalization",
            "preview_id": preview_id,
        }

    finalization["status"] = "in_progress"
    finalization["attempts"] = int(finalization.get("attempts") or 0) + 1
    finalization["started_at"] = utc_now()
    finalization["last_error"] = None
    finalization["last_step"] = "prepare"
    sidecar_path = _persist_finalization(preview_path, preview_payload, finalization, repo_root=repo_root)

    try:
        resolved_remote = (git_remote or "").strip() or _git_origin_url(repo_root)
        if not resolved_remote:
            raise RuntimeError("Missing git push remote: provide --git-remote / GIT_PUSH_REMOTE or configure origin")
        resolved_branch = (git_branch or "").strip() or _git_current_branch(repo_root)

        commit_paths = _collect_commit_paths(preview_path, preview_payload, repo_root)
        finalization["git"]["candidate_paths"] = commit_paths
        finalization["git"]["remote"] = resolved_remote
        finalization["git"]["branch"] = resolved_branch

        commit_state = finalization["git"].get("commit")
        if not isinstance(commit_state, dict):
            commit_state = {}
            finalization["git"]["commit"] = commit_state

        commit_hash = str(commit_state.get("commit_hash") or "").strip()
        if commit_state.get("status") != "success" or not commit_hash:
            if not commit_paths:
                raise RuntimeError("No commit paths resolved for processed preview")

            add_proc = _run_git(repo_root, ["add", "-f", "--", *commit_paths])
            if add_proc.returncode != 0:
                raise RuntimeError(
                    "git add failed: " + ((add_proc.stderr or add_proc.stdout or "").strip()[:300] or "unknown error")
                )
            finalization["git"]["add"] = {
                "status": "success",
                "paths": commit_paths,
            }
            staged_proc = _run_git(repo_root, ["diff", "--cached", "--name-only", "--", *commit_paths])
            if staged_proc.returncode != 0:
                raise RuntimeError("git diff --cached failed")
            staged_paths = [line.strip() for line in staged_proc.stdout.splitlines() if line.strip()]
            finalization["git"]["staged_paths"] = staged_paths
            if not staged_paths:
                raise RuntimeError("No staged changes found for processed preview")

            source = preview_payload.get("source")
            origin_id = source.get("origin_id") if isinstance(source, dict) else None
            commit_message = f"Finalize processed preview {preview_id}"
            if isinstance(origin_id, str) and origin_id.strip():
                commit_message += f" ({origin_id})"
            commit_proc = _run_git(repo_root, ["commit", "-m", commit_message])
            if commit_proc.returncode != 0:
                raise RuntimeError(
                    "git commit failed: "
                    + ((commit_proc.stderr or commit_proc.stdout or "").strip()[:300] or "unknown error")
                )
            rev_proc = _run_git(repo_root, ["rev-parse", "HEAD"])
            if rev_proc.returncode != 0:
                raise RuntimeError("git rev-parse HEAD failed after commit")
            commit_hash = rev_proc.stdout.strip()
            finalization["git"]["commit"] = {
                "status": "success",
                "commit_hash": commit_hash,
                "commit_message": commit_message,
            }
            finalization["last_step"] = "git_commit"
            _persist_finalization(preview_path, preview_payload, finalization, repo_root=repo_root)

        push_state = finalization["git"].get("push")
        if not isinstance(push_state, dict):
            push_state = {}
            finalization["git"]["push"] = push_state

        if push_state.get("status") != "success":
            push_proc = _run_git(repo_root, ["push", resolved_remote, f"{commit_hash}:refs/heads/{resolved_branch}"])
            if push_proc.returncode != 0:
                finalization["git"]["push"] = {
                    "status": "failed",
                    "remote": resolved_remote,
                    "branch": resolved_branch,
                    "commit_hash": commit_hash,
                    "stdout_tail": (push_proc.stdout or "")[-300:],
                    "stderr_tail": (push_proc.stderr or "")[-300:],
                    "returncode": push_proc.returncode,
                }
                raise RuntimeError(
                    "git push failed: "
                    + ((push_proc.stderr or push_proc.stdout or "").strip()[:300] or "unknown error")
                )
            finalization["git"]["push"] = {
                "status": "success",
                "remote": resolved_remote,
                "branch": resolved_branch,
                "commit_hash": commit_hash,
            }
            finalization["last_step"] = "git_push"
            _persist_finalization(preview_path, preview_payload, finalization, repo_root=repo_root)

        trello_state = finalization.get("trello")
        if not isinstance(trello_state, dict):
            trello_state = {}
            finalization["trello"] = trello_state

        if trello_state.get("status") != "success":
            auth = _trello_auth()
            api_key = auth["api_key"]
            api_token = auth["api_token"]
            if not api_key or not api_token:
                raise RuntimeError("Missing Trello write credentials")

            external = preview_payload.get("external_input")
            metadata = external.get("metadata") if isinstance(external, dict) else {}
            board_id = str(metadata.get("board_id") or "").strip() if isinstance(metadata, dict) else ""
            from_list_id = str(metadata.get("list_id") or "").strip() if isinstance(metadata, dict) else ""
            card_id = str(metadata.get("card_id") or "").strip() if isinstance(metadata, dict) else ""
            if not board_id or not card_id:
                raise RuntimeError("Processed preview is missing Trello board/card metadata")

            done_id, resolution = _resolve_done_list_id(
                board_id=board_id,
                done_list_id=trello_done_list_id,
                done_list_name=trello_done_list_name,
                requests_get=requests_get,
            )
            if not done_id:
                raise RuntimeError("Resolved Trello Done list id is empty")

            put_resp = requests_put(
                f"https://api.trello.com/1/cards/{card_id}",
                params={
                    "key": api_key,
                    "token": api_token,
                    "idList": done_id,
                },
                timeout=20,
            )
            if put_resp.status_code != 200:
                trello_state = {
                    "status": "failed",
                    "card_id": card_id,
                    "from_list_id": from_list_id,
                    "done_list_id": done_id,
                    "resolution": resolution,
                    "http_status": put_resp.status_code,
                    "response_preview": (put_resp.text or "")[:300],
                }
                finalization["trello"] = trello_state
                raise RuntimeError(
                    f"Trello update failed: HTTP {put_resp.status_code}; response_preview={(put_resp.text or '')[:300]}"
                )

            trello_state = {
                "status": "success",
                "card_id": card_id,
                "from_list_id": from_list_id,
                "done_list_id": done_id,
                "resolution": resolution,
            }
            finalization["trello"] = trello_state
            finalization["last_step"] = "trello_done"

        finalization["status"] = "completed"
        finalization["completed_at"] = utc_now()
        finalization["last_error"] = None
        _persist_finalization(preview_path, preview_payload, finalization, repo_root=repo_root)
        return {
            "status": "completed",
            "decision_reason": "git_push_and_trello_done_succeeded",
            "preview_id": preview_id,
            "finalization_sidecar": str(sidecar_path),
            "commit_hash": finalization["git"]["commit"]["commit_hash"],
            "done_list_id": finalization["trello"]["done_list_id"],
        }
    except Exception as exc:
        finalization["status"] = "failed"
        finalization["failed_at"] = utc_now()
        finalization["last_error"] = str(exc)
        _persist_finalization(preview_path, preview_payload, finalization, repo_root=repo_root)
        return {
            "status": "failed",
            "decision_reason": str(exc),
            "preview_id": preview_id,
            "finalization_sidecar": str(sidecar_path),
        }


def load_previews(preview_id: str | None) -> list[Path]:
    if preview_id:
        target = PREVIEW_DIR / f"{preview_id}.json"
        return [target] if target.exists() else []
    return sorted(PREVIEW_DIR.glob("*.json"))


def main() -> int:
    args = parse_args()
    previews = load_previews(args.preview_id)
    if not previews:
        print(json.dumps({"status": "idle", "message": "No preview files found."}, ensure_ascii=False))
        return 0

    results = []
    for preview_path in previews:
        results.append(
            process_preview(
                preview_path,
                repo_root=REPO_ROOT,
                git_remote=args.git_remote,
                git_branch=args.git_branch,
                trello_done_list_id=args.trello_done_list_id,
                trello_done_list_name=args.trello_done_list_name,
                allow_replay_finalization=args.allow_replay_finalization,
            )
        )

    payload = {
        "status": "done",
        "completed": len([r for r in results if r["status"] == "completed"]),
        "failed": len([r for r in results if r["status"] == "failed"]),
        "skipped": len([r for r in results if r["status"] == "skipped"]),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
