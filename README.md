<div align="center">
  <h1>🎙️ Vox-Voice</h1>
  <p><strong>Offline-First Voice-OS for Linux / Wayland / COSMIC Interfaces.</strong></p>
  <a href="https://github.com/Jas0nOW/Vox-Voice">View Repository</a>
</div>

---

**Vox-Voice** acts as the high-fidelity acoustic interface ("The Senses") for the WANDA Ecosystem. It is a Siri/Orb-style Voice-OS explicitly designed for modern Linux desktop environments. 

It provides an advanced real-time audio pipeline prioritizing low latency, barge-in (interrupt capabilities), and seamless integration with existing desktop applications via `layer-shell` and `evdev`.

## ✨ Key Features

- **Real-Time Audio Pipeline:** Built for minimal latency featuring active barge-in and echo cancellation (design implementation).
- **Offline-First Capabilities:** Capable of running STT (Speech-to-Text) and TTS (Text-to-Speech) entirely on local hardware (e.g., via Whisper or Kokoro), protecting user privacy out-of-the-box.
- **Typed Event Bus:** All internal communication is strictly typed with `session_id` tracing for robust error tracking and state management.
- **Deep Observability:** Support for Chrome Trace JSON / Perfetto import and optional OpenTelemetry (OTEL) spans for precise audio pipeline debugging.
- **UI Integrations:** Includes an "Orb" desktop overlay crafted with GTK4 and `gtk4-layer-shell`.
- **LLM Agnostic:** Defaults to the powerful Gemini CLI bridge but fully supports local Ollama endpoints for completely offline interactions.

## 🚀 Quick Start (Dev/Sim Mode)

The repository ships with a **simulation mode**, allowing you to validate events, traces, and the run-manifest without complex audio hardware dependencies.

### 1) Start the Voice Engine (Backend)

```bash
cd backend/voice-engine
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .

# Starts the WebSocket gateway on port 7777 (Sim Mode)
voice-engine --mode sim --config config/default.json --ws-host 127.0.0.1 --ws-port 7777 --autostart
```

### 2) Run the Orb Overlay (Frontend)

```bash
cd ../../frontend/orb
python -m venv .venv && source .venv/bin/activate
pip install -U pip websockets

# Connects to the event and command WebSockets
python orb.py --ws ws://127.0.0.1:7777/ws/events --cmd ws://127.0.0.1:7777/ws/command
```

## 🐛 Debugging & Validation

```bash
# Start the voice loop with active --debug flag printing detailed state outputs
./scripts/start_debug.sh

# Complete system validation checks
./scripts/validate_basics.sh
```

## 📚 Technical Documentation & Architecture

For deep-dives into our low-latency goals and architecture decisions:

- **Architecture Overview:** `docs/00_overview/SYSTEM_DESIGN.md`
- **SOTA Research:** `docs/01_research/SOTA_OPTIONS.md`
- **Internal Specs:** `docs/05_specs/` (Orb/MCC/DevContext/DSP)
- **Roadmap:** `docs/04_plan/`

## ⚖️ License
MIT

---
*Built under the JANNIS PROTOCOL — Code Must Be Tested, Efficient, and Secure.*
