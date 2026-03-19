#!/usr/bin/env bash
set -u

STRICT=0
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=1
fi

echo "== Phase 7.1 OCR Environment Check =="
echo "timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "python: $(command -v python3 || echo 'missing')"

MISSING_COUNT=0

echo
echo "[Python modules]"
python3 - <<'PY'
import importlib
modules = [
    "pandas",
    "pytesseract",
    "pdf2image",
    "pypdf",
    "openpyxl",
]
missing = 0
for m in modules:
    try:
        mod = importlib.import_module(m)
        ver = getattr(mod, "__version__", "unknown")
        print(f"OK      {m:<12} version={ver}")
    except Exception as e:
        missing += 1
        print(f"MISSING {m:<12} reason={e}")
print(f"__MISSING_MODULES__={missing}")
PY

MODULE_MISSING=$(python3 - <<'PY'
import importlib
modules = ["pandas", "pytesseract", "pdf2image", "pypdf", "openpyxl"]
missing = 0
for m in modules:
    try:
        importlib.import_module(m)
    except Exception:
        missing += 1
print(missing)
PY
)
MISSING_COUNT=$((MISSING_COUNT + MODULE_MISSING))

echo
echo "[System binaries]"
for b in tesseract pdftoppm; do
  if command -v "$b" >/dev/null 2>&1; then
    echo "OK      $b -> $(command -v "$b")"
  else
    echo "MISSING $b"
    MISSING_COUNT=$((MISSING_COUNT + 1))
  fi
done

echo
echo "missing_total=$MISSING_COUNT"
if [[ "$STRICT" -eq 1 && "$MISSING_COUNT" -gt 0 ]]; then
  exit 1
fi
exit 0
