#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/app")

from skills.delegate_task import delegate_task

BASE_DIR = Path("/app")
CHAIN_WORKSPACE = BASE_DIR / "workspaces" / "manager" / "PHASE6-CHAIN-001"


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_automation_task(task_id):
    return {
        "task_id": task_id,
        "worker": "automation",
        "task_type": "generate_script",
        "objective": "Generate a chain-triggered script artifact for explicit automation->critic flow.",
        "inputs": {"params": {"script_name": f"{task_id.lower()}_script.py"}},
        "expected_outputs": [
            {"path": f"artifacts/scripts/{task_id.lower()}_script.py", "type": "script"}
        ],
        "constraints": ["chain runner explicit invocation", "must be contract compliant"],
        "source": {"kind": "manual", "card_title": "phase6_chain_runner"},
        "metadata": {"phase": "phase6", "chain": "automation_to_critic"},
    }


def build_critic_task(task_id, upstream_artifact):
    return {
        "task_id": task_id,
        "worker": "critic",
        "task_type": "review_artifact",
        "objective": "Review upstream automation artifact generated in explicit chain mode.",
        "inputs": {"artifacts": [{"path": upstream_artifact, "type": "script"}]},
        "expected_outputs": [
            {"path": f"artifacts/reviews/{task_id.lower()}_review.md", "type": "review"}
        ],
        "constraints": ["must reference upstream artifact path", "must be contract compliant"],
        "source": {"kind": "manual", "card_title": "phase6_chain_runner"},
        "metadata": {"phase": "phase6", "chain": "automation_to_critic"},
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--automation-task-id", default="AUTO-20260319-620")
    parser.add_argument("--critic-task-id", default="CRITIC-20260319-621")
    parser.add_argument("--test-mode", default="success")
    return parser.parse_args()


def main():
    args = parse_args()
    CHAIN_WORKSPACE.mkdir(parents=True, exist_ok=True)

    automation_payload = build_automation_task(args.automation_task_id)
    automation_result = delegate_task(
        "automation",
        automation_payload,
        timeout=180,
        retry_attempts=0,
        test_mode=args.test_mode,
    )

    if automation_result.get("status") != "success":
        chain_result = {
            "chain_status": "failed",
            "reason": "automation did not succeed",
            "automation": automation_result,
            "timestamp": utc_now(),
        }
    else:
        upstream_artifact = automation_result["artifacts"][0]["path"]
        critic_payload = build_critic_task(args.critic_task_id, upstream_artifact)
        critic_result = delegate_task(
            "critic",
            critic_payload,
            timeout=180,
            retry_attempts=0,
            test_mode=args.test_mode,
        )
        chain_result = {
            "chain_status": "success" if critic_result.get("status") == "success" else "failed",
            "automation": automation_result,
            "critic": critic_result,
            "upstream_artifact": upstream_artifact,
            "timestamp": utc_now(),
        }

    chain_file = CHAIN_WORKSPACE / "chain_result.json"
    with open(chain_file, "w") as f:
        json.dump(chain_result, f, indent=2, ensure_ascii=False)

    print(json.dumps({"chain_result": chain_result, "chain_file": str(chain_file)}, ensure_ascii=False))
    return 0 if chain_result["chain_status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
