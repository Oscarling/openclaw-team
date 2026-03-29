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

KEY_RE = re.compile(r"(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{20,})")
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
TIMEOUT_TEXT_MARKERS = ("timed out", "timeout")
TLS_EOF_TEXT_MARKERS = ("eof occurred in violation of protocol", "unexpected_eof_while_reading")
DNS_TEXT_MARKERS = (
    "nodename nor servname provided",
    "name or service not known",
    "temporary failure in name resolution",
)
KEY_TEXT_FILE_SUFFIXES = {".rtf", ".txt", ".md", ".env", ".json", ""}


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.is_dir():
        chunks: List[str] = []
        for child in sorted(path.iterdir(), key=lambda item: item.name):
            if child.is_dir():
                chunks.append(load_text(child))
                continue
            if child.suffix.lower() not in KEY_TEXT_FILE_SUFFIXES:
                continue
            chunks.append(load_text(child))
        return "\n".join(part for part in chunks if part)
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


def select_keys_for_endpoints(keys: Sequence[str], endpoints: Sequence[str], probe_all_keys: bool) -> List[str]:
    if probe_all_keys:
        return list(keys)
    if any("generativelanguage.googleapis.com" in (endpoint or "") for endpoint in endpoints):
        gemini_keys = [key for key in keys if key.startswith("AIza")]
        if gemini_keys:
            return gemini_keys[:1]
    return list(keys[:1])


def infer_wire_api(endpoint: str) -> str:
    lowered = (endpoint or "").strip().lower().rstrip("/")
    if lowered.endswith("/chat/completions"):
        return "chat_completions"
    if lowered.endswith("/responses"):
        return "responses"
    return "responses"


def build_probe_payload(model: str, input_text: str, endpoint: str) -> dict:
    wire_api = infer_wire_api(endpoint)
    if wire_api == "chat_completions":
        return {
            "model": model,
            "messages": [{"role": "user", "content": input_text}],
        }
    return {"model": model, "input": input_text}


def probe_once(endpoint: str, key: str, model: str, input_text: str, timeout: int) -> tuple[str, str, str]:
    payload = json.dumps(build_probe_payload(model=model, input_text=input_text, endpoint=endpoint)).encode("utf-8")
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
            return str(resp.getcode()), body, str(resp.headers.get("Content-Type", ""))
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        body = (raw or b"").decode("utf-8", errors="replace")
        return str(exc.code), body, str(exc.headers.get("Content-Type", ""))
    except Exception as exc:  # network/DNS/TLS etc.
        return "000", str(exc), ""


def body_snippet(text: str, limit: int = 180) -> str:
    cleaned = (text or "").replace("\n", " ").replace("\t", " ").strip()
    return cleaned[:limit]


def note_api_like_flag(note: str) -> str:
    lowered = (note or "").lower()
    if "api_like=true" in lowered:
        return "1"
    if "api_like=false" in lowered:
        return "0"
    return "0"


def is_api_like_success(http_code: str, content_type: str, body: str) -> bool:
    code = (http_code or "").strip()
    if not code.isdigit() or not (200 <= int(code) < 300):
        return False
    lowered_ct = (content_type or "").lower()
    if "application/json" in lowered_ct:
        return True
    payload = (body or "").strip()
    if not payload:
        return False
    if payload[0] not in "{[":
        return False
    try:
        parsed = json.loads(payload)
    except Exception:
        return False
    return isinstance(parsed, (dict, list))


def is_retryable_probe_failure(http_code: str, body: str) -> bool:
    code = (http_code or "").strip()
    if code.isdigit():
        value = int(code)
        if 200 <= value < 300:
            return False
        if 400 <= value < 500:
            return False
        if 500 <= value < 600:
            return True
    reason = classify_retry_reason(http_code, body)
    return reason in {"timeout", "tls_eof", "dns_resolution", "transport_other"}


def classify_retry_reason(http_code: str, body: str) -> str:
    code = (http_code or "").strip()
    if code.isdigit() and 500 <= int(code) < 600:
        return "http_5xx"
    lowered = (body or "").lower()
    if any(marker in lowered for marker in TIMEOUT_TEXT_MARKERS):
        return "timeout"
    if any(marker in lowered for marker in TLS_EOF_TEXT_MARKERS):
        return "tls_eof"
    if any(marker in lowered for marker in DNS_TEXT_MARKERS):
        return "dns_resolution"
    if code == "000":
        return "transport_other"
    return "other"


def probe_with_retry(
    endpoint: str,
    key: str,
    model: str,
    input_text: str,
    timeout: int,
    retry_attempts: int,
    probe_func: Callable[[str, str, str, str, int], Tuple[str, str, str]],
) -> Tuple[str, str, str, int, str]:
    attempts = max(1, retry_attempts)
    retry_reasons: List[str] = []
    code, body, content_type = probe_func(endpoint, key, model, input_text, timeout)
    for _ in range(1, attempts):
        if not is_retryable_probe_failure(code, body):
            break
        retry_reasons.append(classify_retry_reason(code, body))
        code, body, content_type = probe_func(endpoint, key, model, input_text, timeout)
    return code, body, content_type, len(retry_reasons), ",".join(retry_reasons)


def build_probe_rows(
    keys: Sequence[str],
    endpoints: Sequence[str],
    model: str,
    input_text: str,
    timeout: int,
    retry_attempts: int = 1,
    probe_func: Callable[[str, str, str, str, int], Tuple[str, str, str]] | None = None,
) -> List[Tuple[str, str, str, str, str, str, str]]:
    if probe_func is None:
        probe_func = probe_once
    rows: List[Tuple[str, str, str, str, str, str, str]] = []
    if not keys:
        for endpoint in endpoints:
            rows.append((endpoint, model, input_text, "000", "missing_key", "0", ""))
        return rows

    for key in keys:
        masked = f"***{key[-6:]}"
        for endpoint in endpoints:
            code, body, content_type, retry_count, retry_reasons = probe_with_retry(
                endpoint=endpoint,
                key=key,
                model=model,
                input_text=input_text,
                timeout=timeout,
                retry_attempts=retry_attempts,
                probe_func=probe_func,
            )
            api_like = is_api_like_success(code, content_type, body)
            rows.append(
                (
                    endpoint,
                    model,
                    input_text,
                    code,
                    "key="
                    + masked
                    + f"; api_like={'true' if api_like else 'false'}; content_type={(content_type or '').strip()}; "
                    + body_snippet(body),
                    str(retry_count),
                    retry_reasons,
                )
            )
    return rows


def count_success_codes(rows: Sequence[Tuple[str, ...]]) -> int:
    total = 0
    for row in rows:
        code = row[3]
        note = row[4]
        if not (code.isdigit() and 200 <= int(code) < 300):
            continue
        lowered_note = (note or "").lower()
        if "api_like=" in lowered_note and "api_like=true" not in lowered_note:
            continue
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
        "--retry-attempts",
        type=int,
        default=2,
        help="Max attempts per endpoint/key for retryable failures (min 1).",
    )
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
    if args.retry_attempts < 1:
        print("--retry-attempts must be >= 1", file=sys.stderr)
        return 2
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    key_files = args.key_file or DEFAULT_KEY_FILES
    endpoints = args.endpoint or DEFAULT_ENDPOINTS
    keys = load_keys(key_files)

    selected_keys = select_keys_for_endpoints(keys=keys, endpoints=endpoints, probe_all_keys=args.probe_all_keys)
    rows = build_probe_rows(
        keys=selected_keys,
        endpoints=endpoints,
        model=args.model,
        input_text=args.input,
        timeout=args.timeout,
        retry_attempts=args.retry_attempts,
    )

    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("endpoint\tmodel\tprobe\thttp_code\tnote\tapi_like\tretry_count\tretry_reasons\n")
        for endpoint, model, probe, code, note, retry_count, retry_reasons in rows:
            handle.write(
                f"{endpoint}\t{model}\t{probe}\t{code}\t{note}\t{note_api_like_flag(note)}\t{retry_count}\t{retry_reasons}\n"
            )

    print(output_path)
    if args.require_success and count_success_codes(rows) == 0:
        print("No successful (2xx + api_like) probe rows detected.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
