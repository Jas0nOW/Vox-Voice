#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

echo "[wanda] bootstrap_linux.sh"
echo "[wanda] root: ${ROOT}"

if [[ "$(type -t python 2>/dev/null || true)" == "alias" ]]; then
  echo "[wanda] WARNING: shell alias detected for 'python'. Consider: unalias python" >&2
  echo "[wanda] WARNING: bootstrap uses explicit venv python path and ignores shell aliases." >&2
fi

SYSTEM_PY312="/usr/bin/python3.12"
SYSTEM_PY3="/usr/bin/python3"

if [[ -n "${WANDA_PYTHON:-}" ]]; then
  PY="${WANDA_PYTHON}"
  if [[ ! -x "${PY}" ]]; then
    echo "[wanda] ERROR: WANDA_PYTHON is not executable: ${PY}" >&2
    exit 2
  fi
elif [[ -x "${SYSTEM_PY312}" ]]; then
  PY="${SYSTEM_PY312}"
elif [[ -x "${SYSTEM_PY3}" ]]; then
  PY="${SYSTEM_PY3}"
else
  echo "[wanda] ERROR: no suitable python interpreter found (need python3.12 or python3)." >&2
  echo "[wanda] On Debian/Ubuntu install required packages:" >&2
  echo "[wanda]   sudo apt-get update && sudo apt-get install -y python3-venv python3-full" >&2
  exit 2
fi

if [[ -z "${WANDA_PYTHON:-}" && "${PY}" == *linuxbrew* ]]; then
  echo "[wanda] WARNING: linuxbrew python detected (${PY}); forcing system python." >&2
  if [[ -x "${SYSTEM_PY312}" ]]; then
    PY="${SYSTEM_PY312}"
  elif [[ -x "${SYSTEM_PY3}" ]]; then
    PY="${SYSTEM_PY3}"
  else
    echo "[wanda] ERROR: system python not found under /usr/bin." >&2
    echo "[wanda] Install required packages, then rerun bootstrap:" >&2
    echo "[wanda]   sudo apt-get update && sudo apt-get install -y python3-venv python3-full" >&2
    exit 2
  fi
fi
echo "[wanda] using interpreter: ${PY}"

VENV=".venv"
VENV_PY="$PWD/.venv/bin/python"

apt_hint() {
  echo "[wanda] On Debian/Ubuntu install required packages:" >&2
  echo "[wanda]   sudo apt-get update && sudo apt-get install -y python3-venv python3-full" >&2
  echo "[wanda] If you target Python 3.12 explicitly:" >&2
  echo "[wanda]   sudo apt-get install -y python3.12 python3.12-venv python3.12-full" >&2
  echo "[wanda] Then rerun: bash scripts/bootstrap_linux.sh" >&2
}

create_venv() {
  local py_bin="$1"
  echo "[wanda] creating venv (copies): ${VENV}"
  if ! "${py_bin}" -m venv --copies "${VENV}"; then
    echo "[wanda] ERROR: failed to create venv." >&2
    apt_hint
    exit 2
  fi
}

VALIDATION_REASON=""
VALIDATION_DETAIL=""

validate_venv() {
  local out=""
  set +e
  out="$("${VENV_PY}" -c "import sys; print(sys.prefix); print(sys.base_prefix)" 2>&1)"
  local rc=$?
  set -e

  if [[ ${rc} -ne 0 ]]; then
    if echo "${out}" | grep -Eq "error while loading shared libraries: libpython|libpython[0-9]+\.[0-9]+\.so"; then
      VALIDATION_REASON="libpython_missing"
    elif echo "${out}" | grep -q "No module named 'encodings'"; then
      VALIDATION_REASON="encodings_missing"
    else
      VALIDATION_REASON="python_runtime_error"
    fi
    VALIDATION_DETAIL="${out}"
    return 1
  fi

  local prefix base
  prefix="$(printf '%s\n' "${out}" | sed -n '1p')"
  base="$(printf '%s\n' "${out}" | sed -n '2p')"

  if [[ -z "${prefix}" || -z "${base}" ]]; then
    VALIDATION_REASON="prefix_parse_failed"
    VALIDATION_DETAIL="${out}"
    return 1
  fi

  if [[ "${prefix}" == "${base}" ]]; then
    VALIDATION_REASON="prefix_equals_base"
    VALIDATION_DETAIL="sys.prefix=${prefix} sys.base_prefix=${base}"
    return 1
  fi

  VALIDATION_REASON="ok"
  VALIDATION_DETAIL="sys.prefix=${prefix} sys.base_prefix=${base}"
  return 0
}

if [[ ! -x "${VENV_PY}" ]]; then
  create_venv "${PY}"
fi

if ! validate_venv; then
  echo "[wanda] WARNING: broken venv detected (${VALIDATION_REASON}), recreating..." >&2
  rm -rf "${VENV}"
  RETRY_PY="${SYSTEM_PY312}"
  if [[ ! -x "${RETRY_PY}" ]]; then
    RETRY_PY="${SYSTEM_PY3}"
  fi
  if [[ ! -x "${RETRY_PY}" ]]; then
    echo "[wanda] ERROR: cannot recreate venv, system python missing in /usr/bin." >&2
    apt_hint
    exit 3
  fi
  echo "[wanda] retry interpreter: ${RETRY_PY}"
  create_venv "${RETRY_PY}"
  if ! validate_venv; then
    echo "[wanda] ERROR: venv still broken after recreate (${VALIDATION_REASON})." >&2
    if [[ -n "${VALIDATION_DETAIL}" ]]; then
      echo "[wanda] Detail: ${VALIDATION_DETAIL}" >&2
    fi
    apt_hint
    exit 3
  fi
fi
echo "[wanda] venv validated: ${VALIDATION_DETAIL}"

echo "[wanda] ensuring pip in venv..."
if ! "${VENV_PY}" -m ensurepip --upgrade; then
  echo "[wanda] ERROR: ensurepip failed inside venv." >&2
  apt_hint
  exit 4
fi

echo "[wanda] upgrading pip/setuptools/wheel in venv..."
"${VENV_PY}" -m pip install -U pip setuptools wheel

echo "[wanda] installing requirements (runtime + dev)..."
"${VENV_PY}" -m pip install -r "${ROOT}/requirements.txt" -r "${ROOT}/requirements-dev.txt"

echo "[wanda] installing wandavoice editable..."
"${VENV_PY}" -m pip install -e .

echo "[wanda] verifying imports..."
if ! "${VENV_PY}" -c "import wandavoice"; then
  echo "[wanda] ERROR: import wandavoice failed." >&2
  exit 4
fi

set +e
SOUND_OUT="$("${VENV_PY}" - <<'PY'
import sys

try:
    import sounddevice as sd  # noqa: F401
    sd.query_devices()
except Exception as e:
    print(f"[wanda] ERROR: sounddevice check failed: {e}", file=sys.stderr)
    try:
        from wandavoice.audio_diagnostics import diagnose_audio, format_audio_diag
        print(format_audio_diag(diagnose_audio()), file=sys.stderr)
    except Exception as inner:
        print(f"[wanda] ERROR: audio diagnostics unavailable: {inner}", file=sys.stderr)
    raise SystemExit(5)
print("OK")
PY
)"
SOUND_RC=$?
set -e
if [[ ${SOUND_RC} -ne 0 ]]; then
  printf '%s\n' "${SOUND_OUT}" >&2
  exit 5
fi
printf '%s\n' "${SOUND_OUT}"

echo "[wanda] OK"
echo "[wanda] Next:"
echo "[wanda]   ${VENV}/bin/wanda voice doctor"
echo "[wanda]   ${VENV}/bin/wanda voice install"
