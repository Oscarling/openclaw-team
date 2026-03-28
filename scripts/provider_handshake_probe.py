#!/usr/bin/env python3
"""Probe provider responses endpoints and write a reproducible TSV matrix.

This script is designed for no-key wait-mode hardening and BL route onboarding.
It intentionally never prints full keys.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, List, Sequence, Tuple

KEY_RE = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
DEFAULT_ENDPOINTS = [
    "https://aixj.vip/v1/responses",
    "https://aixj.vip/responses",
    "https://fast.vpsairobot.com/v1/responses",
    "https://fast.vpsairobot.com/responses",
]
DEFAULT_KEY_FILES = [
    "~/Desktop/备用key3",
    "~/Desktop/备用key3.rtf",
    "~/Desktop/备用key2",
    "~/Desktop/备用key2.rtf",
    "~/Desktop/备用key",
    "~/Desktop/备用key.rtf",
]


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.suffix.lower() == ".rtf":
        try:
            return subprocess.check_output(
                ["textutil", "-convert", "txt", "-stdout", str(path)],
                text=True,
                errors="ignore",
            )
        except Exception:
            return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_keys(text: str) -> List[str]:
    seen = set()
    keys: List[str] = []
    for key in KEY_RE.findall(text or ""):
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def load_keys(paths: Iterable[str]) -> List[str]:
    text = ""
    for raw in paths:
        text += load_text(Path(raw).expanduser())
    return extract_keys(text)


def probe_once(endpoint: str, key: str, model: str, input_text: str, timeout: int) -> tuple[str, str]:
    payload = json.dumps({"model": model, "input": input_text}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return str(resp.getcode()), body
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        body = (raw or b"").decode("utf-8", errors="replace")
        return str(exc.code), body
    except Exception as exc:  # network/DNS/TLS etc.
        return "000", str(exc)


def body_snippet(text: str, limit: int = 180) -> str:
    cleaned = (text or "").replace("\n", " ").replace("\t", " ").strip()
    return cleaned[:limit]


def build_probe_rows(
    keys: Sequence[str],
    endpoints: Sequence[str],
    model: str,
    input_text: str,
    timeout: int,
    probe_func: Callable[[str, str, str, str, int], Tuple[str, str]] | None = None,
) -> List[Tuple[str, str, str, str, str]]:
    if probe_func is None:
        probe_func = probe_once
    rows: List[Tuple[str, str, str, str, str]] = []
    if not keys:
        for endpoint in endpoints:
            rows.append((endpoint, model, input_text, "000", "missing_key"))
        return rows

    for key in keys:
        masked = f"***{key[-6:]}"
        for endpoint in endpoints:
            code, body = probe_func(endpoint, key, model, input_text, timeout)
            rows.append((endpoint, model, input_text, code, f"key={masked}; {body_snippet(body)}"))
    return rows


def count_success_codes(rows: Sequence[Tuple[str, str, str, str, str]]) -> int:
    total = 0
    for _endpoint, _model, _probe, code, _note in rows:
        if code.isdigit() and 200 <= int(code) < 300:
            total += 1
    return total


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe provider responses endpoints and write TSV evidence")
    parser.add_argument("--key-file", action="append", default=[], help="Key file path (repeatable).")
    parser.add_argument("--endpoint", action="append", default=[], help="Responses endpoint URL (repeatable).")
    parser.add_argument("--model", default="gpt-5-codex")
    parser.add_argument("--input", default="ping")
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument(
        "--output",
        default="runtime_archives/bl100/tmp/provider_handshake_probe.tsv",
        help="Output TSV path.",
    )
    parser.add_argument(
        "--probe-all-keys",
        action="store_true",
        help="Probe every discovered key candidate instead of only the first one.",
    )
    parser.add_argument(
        "--require-success",
        action="store_true",
        help="Exit non-zero when no 2xx row is observed in the output matrix.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    key_files = args.key_file or DEFAULT_KEY_FILES
    endpoints = args.endpoint or DEFAULT_ENDPOINTS
    keys = load_keys(key_files)

    selected_keys = keys if args.probe_all_keys else keys[:1]
    rows = build_probe_rows(
        keys=selected_keys,
        endpoints=endpoints,
        model=args.model,
        input_text=args.input,
        timeout=args.timeout,
    )

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("endpoint\tmodel\tprobe\thttp_code\tnote\n")
        for endpoint, model, probe, code, note in rows:
            handle.write(f"{endpoint}\t{model}\t{probe}\t{code}\t{note}\n")

    print(output_path)
    if args.require_success and count_success_codes(rows) == 0:
        print("No successful (2xx) probe rows detected.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
