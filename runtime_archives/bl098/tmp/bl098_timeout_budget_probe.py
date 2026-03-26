#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path('/Users/lingguozhong/openclaw-team')
os.chdir(REPO)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from dispatcher import worker_runtime as wr

OUT_DIR = REPO / 'runtime_archives' / 'bl098' / 'tmp'
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PROBE = OUT_DIR / 'bl098_timeout_budget_probe.tsv'
OUT_REPEATS = OUT_DIR / 'bl098_timeout_budget_repeats.tsv'


def load_key() -> str:
    text = ''
    cand_files = [
        Path('~/Desktop/备用key2').expanduser(),
        Path('~/Desktop/备用key2.rtf').expanduser(),
        Path('~/Desktop/备用key').expanduser(),
        Path('~/Desktop/备用key.rtf').expanduser(),
    ]
    for p in cand_files:
        if not p.exists():
            continue
        if p.suffix.lower() == '.rtf':
            text += subprocess.check_output(['textutil', '-convert', 'txt', '-stdout', str(p)], text=True, errors='ignore')
        else:
            text += p.read_text(encoding='utf-8', errors='ignore')

    keys = re.findall(r'sk-[A-Za-z0-9_-]{20,}', text)
    if keys:
        return keys[0]

    env_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if env_key.startswith('sk-'):
        return env_key
    return ''


def classify(detail: str, exit_code: int) -> str:
    if exit_code == 0:
        return 'ok'
    d = (detail or '').lower()
    if 'timed out' in d or 'timeout' in d:
        return 'timeout'
    if '502' in d:
        return 'http_502'
    if 'tls' in d and 'eof' in d:
        return 'tls_eof'
    if 'remote end closed' in d or 'remote_closed' in d:
        return 'remote_closed'
    return 'other'


def run_once(task: dict, key: str, endpoint: str, timeout_sec: int, field_limit: int, model_name: str):
    os.environ['ARGUS_AUTOMATION_PROMPT_FIELD_MAX_CHARS'] = str(field_limit)
    os.environ['ARGUS_LLM_MAX_RETRIES'] = '1'
    os.environ['ARGUS_LLM_TIMEOUT_RECOVERY_RETRIES'] = '0'
    os.environ['ARGUS_LLM_TIMEOUT_SECONDS'] = str(timeout_sec)
    for k in ['ARGUS_LLM_FALLBACK_RESPONSE_URLS', 'ARGUS_LLM_FALLBACK_CHAT_URLS', 'ARGUS_LLM_FALLBACK_API_BASES']:
        os.environ.pop(k, None)

    settings = {
        'api_key': key,
        'fallback_api_key': None,
        'api_base': endpoint.rsplit('/responses', 1)[0],
        'wire_api': 'responses',
        'chat_url': wr.normalize_chat_endpoint(endpoint),
        'responses_url': endpoint,
        'endpoint_url': endpoint,
        'model_name': model_name,
    }

    prompt = wr.build_user_prompt(task)
    t0 = time.time()
    try:
        raw = wr.call_llm(wr.load_soul('automation'), prompt, 'automation', settings)
        dt = time.time() - t0
        return {
            'exit_code': 0,
            'detail': 'ok',
            'elapsed_sec': dt,
            'prompt_chars': len(prompt),
            'output_chars': len(raw or ''),
            'class': 'ok',
        }
    except Exception as e:
        dt = time.time() - t0
        detail = str(e).replace('\n', ' ')
        return {
            'exit_code': 1,
            'detail': detail,
            'elapsed_sec': dt,
            'prompt_chars': len(prompt),
            'output_chars': 0,
            'class': classify(detail, 1),
        }


def write_probe(rows):
    with OUT_PROBE.open('w', encoding='utf-8') as f:
        f.write('endpoint\tmodel\tfield_limit\ttimeout_sec\tprompt_chars\texit_code\telapsed_sec\toutput_chars\terror_class\tdetail\n')
        for r in rows:
            f.write(
                '\t'.join(
                    map(
                        str,
                        [
                            r['endpoint'],
                            r['model'],
                            r['field_limit'],
                            r['timeout_sec'],
                            r['prompt_chars'],
                            r['exit_code'],
                            f"{r['elapsed_sec']:.3f}",
                            r['output_chars'],
                            r['class'],
                            r['detail'][:220],
                        ],
                    )
                )
                + '\n'
            )


def write_repeats(rows):
    with OUT_REPEATS.open('w', encoding='utf-8') as f:
        f.write('seq\tendpoint\tmodel\tfield_limit\ttimeout_sec\tprompt_chars\texit_code\telapsed_sec\toutput_chars\terror_class\tdetail\n')
        for r in rows:
            f.write(
                '\t'.join(
                    map(
                        str,
                        [
                            r['seq'],
                            r['endpoint'],
                            r['model'],
                            r['field_limit'],
                            r['timeout_sec'],
                            r['prompt_chars'],
                            r['exit_code'],
                            f"{r['elapsed_sec']:.3f}",
                            r['output_chars'],
                            r['class'],
                            r['detail'][:220],
                        ],
                    )
                )
                + '\n'
            )


def main():
    key = load_key().strip()
    if not key:
        raise SystemExit('missing key in Desktop 备用key2/备用key or OPENAI_API_KEY')

    task = json.loads((REPO / 'runtime_archives' / 'bl094' / 'runtime' / 'automation-task.s01.json').read_text(encoding='utf-8'))

    endpoint = 'https://fast.vpsairobot.com/v1/responses'
    model_name = 'gpt-5-codex'
    field_limit = 1200
    budgets = [120, 180, 240, 300]

    probe_rows = []
    for t in budgets:
        r = run_once(task, key, endpoint, t, field_limit, model_name)
        r.update({'endpoint': endpoint, 'model': model_name, 'field_limit': field_limit, 'timeout_sec': t})
        probe_rows.append(r)

    write_probe(probe_rows)

    success_rows = [r for r in probe_rows if r['exit_code'] == 0]
    repeat_rows = []
    if success_rows:
        best_timeout = sorted(success_rows, key=lambda x: x['timeout_sec'])[0]['timeout_sec']
        for i in range(1, 5):
            r = run_once(task, key, endpoint, best_timeout, field_limit, model_name)
            r.update(
                {
                    'seq': i,
                    'endpoint': endpoint,
                    'model': model_name,
                    'field_limit': field_limit,
                    'timeout_sec': best_timeout,
                }
            )
            repeat_rows.append(r)
        write_repeats(repeat_rows)

    print(OUT_PROBE)
    if repeat_rows:
        print(OUT_REPEATS)
    else:
        print('NO_REPEAT_RUN')


if __name__ == '__main__':
    main()
