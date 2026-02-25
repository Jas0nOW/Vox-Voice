# Wanda Voice — Orb (Siri-style) + Mission Control Center (MCC)

Offline-first Voice-OS for Linux/Wayland/COSMIC with:
- realtime audio pipeline + barge-in + cancellation (design + skeleton)
- typed event bus (`session_id` everywhere)
- observability (Chrome Trace JSON / Perfetto import) + optional OTEL spans
- debug/replay (content-addressed artifacts + run manifests)
- Orb overlay (layer-shell) + MCC control plane (web UI)

> This repo ships a **simulation mode** so you can validate events/trace/run-manifest without audio dependencies.

## Defaults (as requested)
- Audio backend routing: **PipeWire**
- LLM bridge default: **Gemini CLI** (profiles: `fast`/`reasoning`/`auto`)
- Alternative LLM backend: **Ollama** (selectable)

Config: `backend/voice-engine/config/default.json`

### Gemini profiles (exact commands)
- `auto`: `gemini`
- `fast`: `gemini --model gemini-3-flash-preview`
- `reasoning`: `gemini --model gemini-3-pro-preview`

## Quick start (dev/sim mode)

### 1) Start backend (gateway + sim sessions)
```bash
cd backend/voice-engine
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .

# starts WebSocket gateway on :7777
voice-engine --mode sim --config config/default.json --ws-host 127.0.0.1 --ws-port 7777 --autostart
```

### 2) Open MCC (static web UI)
```bash
python -m http.server 5173 --directory ../../frontend/mcc
# open http://127.0.0.1:5173
```

### 3) Run Orb (GTK4 + gtk4-layer-shell)
```bash
cd ../../frontend/orb
python -m venv .venv && source .venv/bin/activate
pip install -U pip websockets
python orb.py --ws ws://127.0.0.1:7777/ws/events --cmd ws://127.0.0.1:7777/ws/command
```

## Debug / Validate

```bash
./scripts/start_debug.sh
./scripts/validate_basics.sh
```

`start_debug.sh` startet den Voice-Loop mit aktivem `--debug` Flag.

## Docs
- `docs/00_overview/SYSTEM_DESIGN.md` — 1–2 page architecture + defaults
- `docs/01_research/SOTA_OPTIONS.md` — option research + recommendations
- `docs/02_architecture/` — events/state, tracing, replay, security
- `docs/04_plan/` — milestones + DoD/acceptance tests
- `docs/05_specs/` — Orb/MCC/DevContext/DSP specs
- `prompts/` — master prompt + implementation prompts

## License
MIT (adjust as needed).
