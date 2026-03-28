#!/usr/bin/env python3
"""One-shot provider onboarding gate: run probe, then run assessment."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE_SCRIPT = REPO_ROOT / "scripts" / "provider_handshake_probe.py"
ASSESS_SCRIPT = REPO_ROOT / "scripts" / "provider_handshake_assess.py"


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
    return parser.parse_args()


def run_command(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

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

    return assess_proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
