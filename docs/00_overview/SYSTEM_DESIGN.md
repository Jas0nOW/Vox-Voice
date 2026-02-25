# System Design (v1)

## Goals (non‑negotiables)
- **Barge-in**: stop playback <100ms; cancel pipeline <250ms.
- **Traceability**: every event/spans keyed by `session_id`.
- **Modular**: wake/VAD/STT/LLM/TTS/UI via adapters.
- **Replay**: every session writes a manifest + content-addressed artifacts.
- **Safety**: skills via allowlist + permissions + confirm flows; dev-context is untrusted.

## Process topology (recommended)
```mermaid
flowchart LR
  VE[voice-engine
(audio+dsp+vad+stt+router+llm+tts+skills)] <-- ws/json --> GW[event-gateway
(FastAPI WS)]
  GW <-- ws --> MCC[MCC
(local web UI)]
  GW <-- ws --> ORB[Orb
(gtk4-layer-shell)]
  VE --> RUNS[runs/
(manifest + cas + traces)]
```

- `voice-engine`: realtime pipeline + state machine + cancellation.
- `event-gateway`: in-process (MVP) WebSocket server for UIs; later swap to NATS/ZeroMQ.
- `ui-orb`: layer-shell overlay; renders at 60fps; subscribes to audio levels + state.
- `ui-mcc`: control plane + tracing + replay + settings + dev-context buffer.

## Data model
### Event envelope
```json
{
  "schema_version": "1.0",
  "event_id": "ulid",
  "session_id": "ulid",
  "ts_unix_ms": 0,
  "component": "vad|stt|router|llm|tts|dsp|ui-orb|ui-mcc|system",
  "type": "vad_start|stt_partial|...",
  "payload": {}
}
```

### Run manifest (one per session)
- `runs/<YYYY-MM-DD>/<session_id>/manifest.json`
- references artifacts in `cas/sha256/<hash>` (wav/flac/json/etc)
- includes config snapshot + model versions + device IDs + DSP params + redaction

## Defaults (recommended)
- Transport: **WebSocket** (MVP) → NATS/ZeroMQ (later).
- Audio backend routing (default): **PipeWire** (capture + playback) with per-device health counters (underruns/overruns).
- DSP (default for speakers mode): PipeWire Pulse `module-echo-cancel` (WebRTC) for fast MVP; later swap to in-engine WebRTC AudioProcessing for per-session parameter logging + deterministic replay.
- Wake (default): **openWakeWord**.
- LLM Bridge (default): **Gemini CLI (persistent process)** with three profiles exposed in MCC:
  - `Fast` → `gemini-3-flash-preview`
  - `Thinking` → `gemini-3-pro-preview`
  - `Auto Reasoning` → Gemini built-in auto gating (bridge passes through a policy flag; exact mechanics are bridge-specific)
  Fallback/Option: **Ollama** (local HTTP) selectable in MCC/Config.
- Tracing: **Chrome Trace JSON** export (Perfetto import) + optional OTEL spans (same `session_id`).
- Dev Context: auto-attach on LLM/chat only; `Attach once and clear` default; token estimate + oversize warning + optional truncate oldest lines.

## Performance budgets (P95)
- Wake → Listening: <150ms
- End speech → STT final: <900ms (profile dependent)
- End speech → First TTS: <1500ms (model dependent)
- Barge-in: stop audio <100ms; cancel pipeline <250ms
