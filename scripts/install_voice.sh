#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[wanda] install_voice.sh"
echo "[wanda] root: ${ROOT}"

if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  PY="${VIRTUAL_ENV}/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="python3"
elif command -v python >/dev/null 2>&1; then
  PY="python"
else
  echo "[wanda] ERROR: python not found in PATH." >&2
  exit 2
fi

if [[ ! -f /etc/os-release ]]; then
  echo "[wanda] ERROR: /etc/os-release not found (unsupported distro detection)." >&2
  exit 2
fi

# shellcheck disable=SC1091
source /etc/os-release
ID_LIKE_LOWER="$(echo "${ID_LIKE:-}" | tr '[:upper:]' '[:lower:]')"
ID_LOWER="$(echo "${ID:-}" | tr '[:upper:]' '[:lower:]')"
OS_BLOB="${ID_LOWER} ${ID_LIKE_LOWER}"

echo "[wanda] detected: ${PRETTY_NAME:-${ID_LOWER}}"

install_portaudio_debian() {
  ${SUDO} apt-get update
  ${SUDO} apt-get install -y libportaudio2 portaudio19-dev
}

install_portaudio_arch() {
  ${SUDO} pacman -S --needed portaudio
}

install_portaudio_fedora() {
  ${SUDO} dnf install -y portaudio portaudio-devel
}

install_portaudio_suse() {
  ${SUDO} zypper install -y portaudio portaudio-devel
}

if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
else
  SUDO=""
  echo "[wanda] WARNING: sudo not found. Run the printed commands as root." >&2
fi

if [[ "${OS_BLOB}" == *"debian"* || "${OS_BLOB}" == *"ubuntu"* || "${OS_BLOB}" == *"pop"* || "${OS_BLOB}" == *"linuxmint"* ]]; then
  install_portaudio_debian
elif [[ "${OS_BLOB}" == *"arch"* ]]; then
  install_portaudio_arch
elif [[ "${OS_BLOB}" == *"fedora"* || "${OS_BLOB}" == *"rhel"* || "${OS_BLOB}" == *"centos"* ]]; then
  install_portaudio_fedora
elif [[ "${OS_BLOB}" == *"suse"* || "${OS_BLOB}" == *"opensuse"* ]]; then
  install_portaudio_suse
else
  echo "[wanda] ERROR: Unsupported distro family for auto-install." >&2
  echo "[wanda] Install PortAudio runtime manually. Examples:" >&2
  echo "[wanda]   Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y libportaudio2 portaudio19-dev" >&2
  echo "[wanda]   Arch: sudo pacman -S --needed portaudio" >&2
  echo "[wanda]   Fedora: sudo dnf install -y portaudio portaudio-devel" >&2
  echo "[wanda]   openSUSE: sudo zypper install -y portaudio portaudio-devel" >&2
  exit 2
fi

echo "[wanda] verifying sounddevice + PortAudio..."
"${PY}" -c "import sounddevice as sd; sd.query_devices(); print('OK: sounddevice query_devices()')"
