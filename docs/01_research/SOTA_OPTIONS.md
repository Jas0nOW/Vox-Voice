# SOTA Options & Recommendations (Feb 2026)

This summarizes the best practical options for Wayland overlay/layer-shell, DSP (AEC/NS/AGC), observability, wake-word, barge-in streaming, and replay/artefacts.

## 1) Wayland overlay / layer-shell (OSD)
**Recommendation (default): GTK4 + gtk4-layer-shell**  
- `gtk4-layer-shell` supports wlr-layer-shell and is usable via GObject introspection (Python/Vala/etc).  
  Ref: https://github.com/wmww/gtk4-layer-shell

Alternatives:
- **Qt/QML** via `layer-shell-qt` (KDE): https://github.com/KDE/layer-shell-qt
- Raw Wayland client using `wlr-layer-shell` protocol: https://wayland.app/protocols/wlr-layer-shell-unstable-v1

COSMIC note: System76 explicitly uses Layer Shell for stability (independent shell components).  
Ref: https://blog.system76.com/post/cosmic-team-interview-byoux/

## 2) DSP (AEC / NS / AGC)
**MVP default: PipeWire module-echo-cancel (WebRTC)**
- PipeWire Pulse module `module-echo-cancel` exposes `aec_method` and related options.  
  Ref: https://docs.pipewire.org/page_pulse_module_echo_cancel.html

**Production / per-session logging: in-engine WebRTC AudioProcessing**
- Rust: `sonora` (pure Rust WebRTC audio processing)  
  Ref: https://github.com/dignifiedquire/sonora
- Rust wrapper: `webrtc-audio-processing` (PulseAudio repackaging of WebRTC AP)  
  Ref: https://docs.rs/crate/webrtc-audio-processing/latest

## 3) Observability (Perfetto + OTEL)
**Recommendation: Chrome Trace JSON export + Perfetto import (MVP)**
- Perfetto can import Chrome Trace JSON (“Trace Event Format”), but requires proper nesting for B/E events.  
  Refs:
  - https://perfetto.dev/docs/getting-started/other-formats
  - https://perfetto.dev/docs/faq
  - https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview

**Add OTEL spans for semantic consistency**
- OTEL trace concepts + context propagation.  
  Refs:
  - https://opentelemetry.io/docs/concepts/signals/traces/
  - https://opentelemetry.io/docs/concepts/context-propagation/
  - https://opentelemetry.io/docs/specs/otel/overview/

## 4) Wake word
**Default: openWakeWord (offline, OSS)**
- Ref: https://github.com/dscripka/openWakeWord  
- Home Assistant also documents wake-word workflows with openWakeWord: https://www.home-assistant.io/voice_control/create_wake_word/

## 5) TTS streaming + barge-in
**Recommendation: chunked streaming + cancel token**
- TTS adapter must implement `cancel(session_id)` which immediately:
  1) stops audio output stream (flush buffer)  
  2) propagates cancellation to upstream tasks (router/llm/tts)
- Keep a dedicated “playback supervisor” task to ensure <100ms stop.

## 6) Debug / replay (content-addressed artifacts)
**Recommendation: CAS (sha256) + run manifests**
- Content-addressed storage is a standard pattern (e.g., Bazel remote cache CAS).  
  Ref: https://bazel.build/remote/caching
- Example of CAS keyed by SHA256 in a Bazel remote cache implementation: https://github.com/buchgr/bazel-remote
## 7) LLM bridge (Gemini CLI default, option: Ollama)
**Recommendation (default): Gemini CLI as a persistent background process**
- Keep a long-lived subprocess, feed prompts via stdin (or a local IPC wrapper), stream tokens back to the engine.
- Emit bridge metrics: `spawn_time_ms`, `first_token_ms`, `total_ms` per request.
- Watchdog: restart on crash; emit `watchdog_restart` with reason.

**Option: Ollama (offline)**
- Use local HTTP (`http://127.0.0.1:11434`) for `/api/generate` streaming.
- Same adapter interface as Gemini bridge; MCC can toggle backend per-session.

Defaults used in this repo:
- Backend: `gemini_cli`
- Profiles exposed in MCC: `Fast` / `Thinking` / `Auto Reasoning`
- Model strings are config values (you can change them without code changes).

## 8) Session replay / artifacts (CAS + manifests)
**Recommendation: content-addressed artifacts (SHA256) + run manifest per session**
- Store audio in/out, transcripts, traces, config snapshot, device IDs, DSP params.
- CAS enables dedup and integrity checks; manifests enable deterministic replay + regression diffs.
