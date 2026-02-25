<div align="center">

# Vox-Voice

**Offline-first voice runtime for Linux and WANDA interfaces**

[![Status](https://img.shields.io/badge/status-active-brightgreen)](./docs/04_plan/HANDOFF.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

</div>

Vox-Voice is the acoustic interface for the WANDA ecosystem.  
It focuses on low-latency voice interaction, typed event flows, and reliable local/offline execution.

## Core Capabilities

- Real-time voice pipeline with barge-in support
- Offline-first STT/TTS options
- Typed event bus with session tracing
- Orb overlay and UI integration layer
- Bridge support for local providers and WANDA workflows

## Repository Layout

| Path | Purpose |
| --- | --- |
| `backend/voice-engine/` | WS gateway and audio engine |
| `frontend/orb/` | Orb overlay client |
| `src/wandavoice/` | Core package and CLI logic |
| `scripts/` | Validation, setup, model helpers |
| `docs/` | Architecture, plan, and operations docs |

## Quick Start (Simulation)

```bash
cd backend/voice-engine
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
voice-engine --mode sim --config config/default.json --ws-host 127.0.0.1 --ws-port 7777 --autostart
```

In a second terminal:

```bash
cd frontend/orb
python -m venv .venv
source .venv/bin/activate
pip install -U pip websockets
python orb.py --ws ws://127.0.0.1:7777/ws/events --cmd ws://127.0.0.1:7777/ws/command
```

## Validation

```bash
./scripts/validate_basics.sh
./scripts/start_debug.sh
```

## Documentation

- [System Design](./docs/00_overview/SYSTEM_DESIGN.md)
- [Architecture](./docs/02_architecture/ARCH.md)
- [Usage](./docs/03_usage/USAGE.md)
- [Tasks](./docs/04_plan/TASKS.md)
- [Handoff](./docs/04_plan/HANDOFF.md)

## Security and Data Hygiene

- Keep `.env` local and untracked
- Keep generated audio artifacts and model caches out of git
- Review `docs/02_architecture/SECURITY.md` before production rollout

## License

MIT. See [LICENSE](./LICENSE).
