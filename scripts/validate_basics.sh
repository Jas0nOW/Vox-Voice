#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -x .venv/bin/python ]]; then
  echo "[vox] missing .venv/bin/python"
  exit 1
fi

echo "[vox] python compile check"
PYTHONPATH=src ./.venv/bin/python -m compileall -q src

echo "[vox] cli help smoke"
PYTHONPATH=src ./.venv/bin/python -m wandavoice.main --help >/dev/null

echo "[vox] dependency smoke (websockets)"
./.venv/bin/python -m pip show websockets >/dev/null

echo "[vox] validate: OK"
