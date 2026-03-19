#!/usr/bin/env bash
set -euo pipefail

echo "== Phase 7.1 Conservative OCR Env Repair =="
echo "timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found"
  exit 2
fi

PY_MISSING=$(
python3 - <<'PY'
import importlib
targets = ["pandas", "pytesseract", "pdf2image", "pypdf", "openpyxl"]
missing = []
for name in targets:
    try:
        importlib.import_module(name)
    except Exception:
        missing.append(name)
print(" ".join(missing))
PY
)

if [[ -n "${PY_MISSING}" ]]; then
  echo "Installing missing Python packages (user scope): ${PY_MISSING}"
  python3 -m pip install --user --upgrade ${PY_MISSING}
else
  echo "No missing Python packages in target set."
fi

echo
echo "System-level OCR binaries are NOT auto-installed by this script."
echo "Run manually if needed:"
echo "  brew update"
echo "  brew install tesseract poppler"
echo
echo "Post-check:"
bash "$(dirname "$0")/check_ocr_env.sh" || true
