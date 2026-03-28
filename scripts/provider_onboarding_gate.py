#!/usr/bin/env python3
"""One-shot provider onboarding gate: run probe, then run assessment."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_SCRIPT = REPO_ROOT / "scripts" / "provider_handshake_probe.py"
ASSESS_SCRIPT = REPO_ROOT / "scripts" / "provider_handshake_assess.py"
SUMMARY_SCRIPT = REPO_ROOT / "scripts" / "provider_onboarding_history_summary.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run provider onboarding gate (probe + assess)")
    parser.add_argument(
        "--output-dir",
        default="runtime_archives/bl100/tmp",
        help="Directory for generated probe/assessment files",
    )
    parser.add_argument(
        "--stamp",
        default=datetime.now().strftime("%Y%m%d"),
        help="Filename stamp (default: today)",
    )
    parser.add_argument("--key-file", action="append", default=[], help="Key file path (repeatable)")
    parser.add_argument("--endpoint", action="append", default=[], help="Endpoint URL (repeatable)")
    parser.add_argument("--model", default="gpt-5-codex")
    parser.add_argument("--input", default="ping")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument(
        "--probe-all-keys",
        action="store_true",
        help="Probe all discovered key candidates",
    )
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Exit non-zero when assessment result is blocked",
    )
    parser.add_argument(
        "--history-jsonl",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history.jsonl",
        help="History jsonl path for appending gate outcomes",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Disable appending history records",
    )
    parser.add_argument(
        "--history-summary-json",
        default="runtime_archives/bl100/tmp/provider_onboarding_gate_history_summary.json",
        help="Output JSON path for refreshed history summary",
    )
    parser.add_argument(
        "--no-history-summary",
        action="store_true",
        help="Skip refreshing history summary after gate run",
    )
    parser.add_argument(
        "--history-summary-repo-only",
        dest="history_summary_repo_only",
        action="store_true",
        default=True,
        help="Refresh summary using only repo-contained evidence entries (default on)",
    )
    parser.add_argument(
        "--no-history-summary-repo-only",
        dest="history_summary_repo_only",
        action="store_false",
        help="Allow non-repo evidence entries when refreshing history summary",
    )
    parser.add_argument(
        "--assessment-snapshot-dir",
        default="runtime_archives/bl100/tmp/provider_handshake_assessment_snapshots",
        help="Directory for immutable per-run assessment snapshots referenced by history rows",
    )
    return parser.parse_args()


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def load_assessment_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def append_history_entry(path: Path, entry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_assessment_snapshot(source: Path, snapshot_dir: Path, stamp: str, run_timestamp: str) -> Optional[Path]:
    if not source.exists():
        return None
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    try:
        suffix = datetime.fromisoformat(run_timestamp).strftime("%Y%m%dT%H%M%S")
    except ValueError:
        suffix = run_timestamp.replace(":", "").replace("-", "").replace(" ", "_")
    target = snapshot_dir / f"provider_handshake_assessment_gate_{stamp}_{suffix}.json"
    shutil.copy2(source, target)
    return target


def refresh_history_summary(history_path: Path, output_json: Path, repo_only: bool) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(SUMMARY_SCRIPT),
        "--history-jsonl",
        str(history_path),
        "--output-json",
        str(output_json),
        "--repo-root",
        str(REPO_ROOT),
    ]
    if repo_only:
        cmd.append("--repo-only")
    return run_command(cmd)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    history_path = Path(args.history_jsonl)
    if not history_path.is_absolute():
        history_path = REPO_ROOT / history_path
    history_summary_path = Path(args.history_summary_json)
    if not history_summary_path.is_absolute():
        history_summary_path = REPO_ROOT / history_summary_path
    snapshot_dir = Path(args.assessment_snapshot_dir)
    if not snapshot_dir.is_absolute():
        snapshot_dir = REPO_ROOT / snapshot_dir

    probe_tsv = out_dir / f"provider_handshake_probe_gate_{args.stamp}.tsv"
    assess_json = out_dir / f"provider_handshake_assessment_gate_{args.stamp}.json"

    probe_cmd = [sys.executable, str(PROBE_SCRIPT), "--output", str(probe_tsv), "--model", args.model, "--input", args.input, "--timeout", str(args.timeout)]
    if args.probe_all_keys:
        probe_cmd.append("--probe-all-keys")
    for key_file in args.key_file:
        probe_cmd.extend(["--key-file", key_file])
    for endpoint in args.endpoint:
        probe_cmd.extend(["--endpoint", endpoint])

    probe_proc = run_command(probe_cmd)
    if probe_proc.stdout:
        print(probe_proc.stdout.strip())
    if probe_proc.stderr:
        print(probe_proc.stderr.strip(), file=sys.stderr)
    if probe_proc.returncode != 0:
        if not args.no_history:
            run_timestamp = datetime.now().isoformat(timespec="seconds")
            append_history_entry(
                history_path,
                {
                    "timestamp": run_timestamp,
                    "stamp": args.stamp,
                    "probe_tsv": str(probe_tsv),
                    "assessment_json": str(assess_json),
                    "exit_code": probe_proc.returncode,
                    "phase": "probe",
                    "status": "probe_failed",
                    "block_reason": "probe_command_failed",
                },
            )
            if not args.no_history_summary:
                summary_proc = refresh_history_summary(
                    history_path,
                    history_summary_path,
                    repo_only=args.history_summary_repo_only,
                )
                if summary_proc.stdout:
                    print(summary_proc.stdout.strip())
                if summary_proc.stderr:
                    print(summary_proc.stderr.strip(), file=sys.stderr)
        return probe_proc.returncode

    assess_cmd = [
        sys.executable,
        str(ASSESS_SCRIPT),
        "--probe-tsv",
        str(probe_tsv),
        "--output-json",
        str(assess_json),
    ]
    if args.require_ready:
        assess_cmd.append("--require-ready")

    assess_proc = run_command(assess_cmd)
    if assess_proc.stdout:
        print(assess_proc.stdout.strip())
    if assess_proc.stderr:
        print(assess_proc.stderr.strip(), file=sys.stderr)
    if not args.no_history:
        run_timestamp = datetime.now().isoformat(timespec="seconds")
        snapshot_path = write_assessment_snapshot(assess_json, snapshot_dir, args.stamp, run_timestamp)
        summary = load_assessment_summary(assess_json)
        append_history_entry(
            history_path,
            {
                "timestamp": run_timestamp,
                "stamp": args.stamp,
                "probe_tsv": str(probe_tsv),
                "assessment_json": str(assess_json),
                "assessment_snapshot_json": str(snapshot_path) if snapshot_path else None,
                "exit_code": assess_proc.returncode,
                "phase": "assess",
                "status": summary.get("status", "unknown"),
                "block_reason": summary.get("block_reason", "unknown"),
                "success_row_count": summary.get("success_row_count"),
                "http_code_counts": summary.get("http_code_counts"),
                "note_class_counts": summary.get("note_class_counts"),
            },
        )
        if not args.no_history_summary:
            summary_proc = refresh_history_summary(
                history_path,
                history_summary_path,
                repo_only=args.history_summary_repo_only,
            )
            if summary_proc.stdout:
                print(summary_proc.stdout.strip())
            if summary_proc.stderr:
                print(summary_proc.stderr.strip(), file=sys.stderr)

    return assess_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
