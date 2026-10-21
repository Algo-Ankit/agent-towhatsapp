#!/usr/bin/env bash
# Mac / Linux / Git Bash: create an isolated virtual environment in .venv and install deps.
# Your global Python is never touched.
set -e
cd "$(dirname "$0")/.."

PY=""
for c in python3.12 python3.11 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
[ -z "$PY" ] && { echo "Python 3.10+ not found. Install it from python.org first."; exit 1; }

if [ ! -d .venv ]; then
  echo "Creating .venv with $($PY --version)..."
  "$PY" -m venv .venv
fi

if [ -f .venv/bin/python ]; then VPY=.venv/bin/python; else VPY=.venv/Scripts/python.exe; fi
"$VPY" -m pip install -q --upgrade pip
"$VPY" -m pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env

echo
echo "Done. Environment is in .venv (isolated from your global Python)."
echo "Activate it in this terminal with:  source .venv/bin/activate"
echo "Then run the demo:                  bash scripts/demo.sh"
