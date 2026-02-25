# PROMPT (MASTER): Wanda Voice — Orb (Siri-Style) + Mission Control Center (MCC)
Plattform: Linux / Wayland / COSMIC • Ziel: 0€, production-ready • Fokus: Realtime-Audio + State Machines + Observability + Debug/Replay + Dev-Assist

---

## 🧠 ROLE (du, die KI)
Du bist gleichzeitig:
1) Senior Staff Engineer (Realtime Audio, DSP, State Machines, Cancel/Barge-in)
2) Product/UX Designer (Orb Immersion, 60fps, Accessibility, Motion/3D)
3) Observability Engineer (Tracing, Perfetto, OTEL, Replay/Regression)
4) Desktop Engineer (Wayland/COSMIC Constraints, layer-shell/OSD)
5) Dev-Workflow Architect (Debug UX, Kontext-Auto-Attach, AI-Assist Integration)

---

## 🎯 NON-NEGOTIABLES (Hard Rules)
- Realtime: **Barge-in** muss funktionieren (Stop speaking <100ms Audio, <250ms Pipeline Cancel).
- Traceability: JEDER Schritt ist tracebar über `session_id`.
- Modular: Alle Engines (Wake/VAD/STT/LLM/TTS/UI) sind austauschbar (Adapter Pattern).
- Debuggability: Jede Session ist replaybar (Golden Runs, Regression Tests).
- Safety: Skills nur via Allowlist + Permissions + Confirm-Flows; Dev-Context ist **untrusted**.

---

## 🧩 CONTEXT (Setup)
- Wake Word + VAD + STT + Router + LLM + TTS + Commands laufen lokal.
- Orb: visuell immersiv, state-aware, audio-reaktiv (60fps Ziel).
- MCC: Mission Control Center als Control-Plane + Observability + Debug + Settings + Dev-Context.
- Bridge: Gemini-CLI läuft optional als unsichtbarer Prozess im Hintergrund.
- OS: Linux (Wayland/COSMIC). Keine X11-Tricks als Abhängigkeit.

---

## ✅ OUTCOME (was du baust)
Ein vollständiges Voice-OS bestehend aus:

A) **ORB** — immersiv, 60fps, state-aware, audio-reactive, minimal UI
B) **MCC** — Control-Plane + Observability + Debug/Replay + Settings + Skills/Permissions
C) **DEV-KONTEXT** — Fehler/Logs/Code/Paths/Terminal automatisch (kontrolliert) in LLM-Anfragen

---

## 🔎 SOTA RESEARCH (Pflicht, bevor du finalisierst)
Mach Web-Research (nicht oberflächlich) zu:
- Wayland overlay/layer-shell patterns (OSD, click-through, multi-monitor)
- Realtime audio DSP: AEC/NS/AGC (PipeWire module-echo-cancel vs WebRTC AudioProcessing)
- Observability: Perfetto/Chrome Trace JSON + OTEL best practices
- Wake word: openWakeWord vs Alternativen
- TTS streaming + barge-in patterns (chunking, cancel tokens)
- Debug/replay: content-addressed artifacts, session manifests

Ergebnis: Liste der besten Optionen, kurze Bewertung, klare Empfehlung + Defaults.

---

# 🏗️ ARCHITEKTUR (GLOBAL)

## 1) Prozess-Topologie (empfohlen)
- **voice-engine** (Backend): Audio capture, DSP, VAD, STT, Router, LLM bridge, TTS, Skills
- **ui-orb** (Frontend): Orb renderer (layer-shell OSD), minimal controls
- **ui-mcc** (Frontend): Panels, tracing viewer, settings, dev context
- **event-gateway** (optional): WebSocket/IPC bridge zwischen engine und UIs
- **multi-Cli** (optional): Gemini ermöglichen Sub Agenten zu Spawnen und nutzen (Erst wenn alles Stabil)

Wichtig: Backend und UI sind strikt entkoppelt über Events + typed schemas.

---

## 2) Event-Driven Core (mit `session_id`)
Definiere einen globalen Event Bus mit `session_id`, `event_id`, `timestamp`, `component`, `payload`.

### Transport (2 Optionen)
- Option A (simpel): In-process event bus + WebSocket für UI
- Option B (robust): ZeroMQ/NATS lokal (0€) für mehrere Prozesse

Empfehlung: A für MVP, B sobald du stabil bist.

### Typed Schemas
- Alle Events als JSON Schema oder Pydantic/TypeBox definieren.
- Versionierung: `schema_version`.

---

## 3) Pipeline Stages (MUSS)
**capture → dsp → wakeword → vad → stt → router → llm → tts → playback**

### DSP Stage (kritisch!)
- AEC (Echo Cancellation) für Speaker-Mode
- NS (Noise Suppression) stabilisiert VAD/STT
- Optional AGC (Gain Control)
- DSP Param-Logging als Events

**MCC benötigt ein eigenes DSP Panel** (siehe unten).

---

# 🎛️ EVENTS (vollständig, erweitert)
Basis:
- audio_level (mic), audio_level_out (tts/playback)
- wake_detected
- vad_start / vad_end
- stt_partial / stt_final
- router_decision
- action_start / action_end
- llm_stream_chunk / llm_done
- tts_start / tts_chunk / tts_stop
- dev_context_attached

Erweitert (neu, Pflicht):
- audio_device_changed
- dsp_state (aec_on, ns_level, agc_mode, echo_likelihood)
- cancel_request (reason: barge_in|user_stop|timeout|router_change)
- cancel_done
- run_manifest_written (artifact refs)
- error_raised (component + stack + code)
- watchdog_restart (component + reason)

---

# 🌀 ORB SPEC (Immersive UX)

## States
- SLEEPING
- WAKE_DETECTED
- LISTENING
- THINKING
- SPEAKING
- MUTED
- ERROR

## Rendering Regeln
- 60fps Ziel (dropped frames zählen + anzeigen im MCC)
- No jitter: smoothing/damping everywhere
- No chaos: motion energy bounded
- Always readable: state cues klar (Form/Motion/Glow; nicht nur Farbe)

## Audio Mapping
- mic_level → wave amplitude (smoothed RMS)
- tts_level → glow expansion / pulse
- state → motion profile + intensity

## Wayland Umsetzung (Realismus!)
- Orb ist ein **layer-shell / OSD-Surface** (nicht “always-on-top hack”).
- Optional click-through (nur wenn sicher/gewollt).
- Multi-Monitor Pinning + Anchor.

Optional:
- Ambient idle mode
- Reduced motion accessibility mode
- Subtle spatial feedback (kurze earcons)

---

# 🧭 MCC SPEC (Mission Control Center)

## Layout
Left Nav:
- Overview
- Conversation
- Audio
- DSP (AEC/NS/AGC) ✅
- Wake Word ✅
- VAD
- STT
- Router
- Skills
- LLM Bridge (Gemini/Ollama)
- TTS / Voices
- Dev Context ✅
- Debug / Replay ✅
- Runs / Artifacts ✅
- Settings
- Logs

Top Bar:
- Global State
- Current `session_id`
- Latency live (P50/P95/P99)
- Quick toggles: Mute, Sleep, Stop, Fast (gemini-3-flash-preview), Thinking (gemini-3-pro-preview), Auto Reasoning (Geminis build in Auto gate)

---

# ✅ PFLICHT-PANELS (ausgearbeitet)

## 1) Conversation Monitor
- Timeline User → Assistant
- Partial + Final transcript (partial einklappbar)
- Copy / Export
- Mark as Golden (für Regression)

## 2) Audio Panel
- Live waveform + RMS/Peak
- Mic/Output selector
- Noise floor calibration wizard
- Pre-roll ring buffer (konfigurierbar, z.B. 2–5s)
- First-word drop detection (Warnung + Counter)
- Device health: underruns/overruns, buffer stats

## 3) DSP Panel (AEC/NS/AGC) ✅
- Mode: Headset / Speakers
- AEC: on/off + aggressiveness
- NS: level + profile
- AGC: on/off + target level
- Echo likelihood meter
- “Test loop”: TTS abspielen, mic leak messen, AEC wirksamkeit loggen
- Events: `dsp_state` live

## 4) Wake Word Panel ✅
- Engine: openWakeWord (Default) + Alternativen (optional)
- Sensitivity/threshold
- False positives pro Stunde
- “Push-to-talk fallback” Hotkey
- Multi wakewords optional (z.B. “Wanda”, “Computer”)
- Wake latency meter

## 5) VAD / Endpointing
- `min_speech_ms`, `end_silence_ms`, `continue_window_ms`
- Profile switch: Command vs Chat
- Live end-prediction preview (“Would end now?”)

Default Startwerte:
- Command: `end_silence_ms` 280–420, `continue_window_ms` 650–900
- Chat: `end_silence_ms` 500–750, `continue_window_ms` 900–1300

## 6) STT Panel
- Model select: fast preview vs final
- Custom vocab bias (Wanda, Produktnamen)
- Confidence + word timestamps
- Confusion tracking (Wanda/Wanderer/…)
- Normalization rules (kontextsensitiv, nicht destruktiv)

## 7) Router Panel
- Command grammar list + synonyms (“stopp/halt/abbrechen”)
- Safety rules: confirm for risky actions
- Decision trace: warum Command vs Chat
- Policy overrides: “Dev mode”, “Quiet mode”, “Handsfree”

## 8) Skills Panel
- Installed skills list
- Recent invocations (duration + status)
- “Dry run” mode
- Permissions per skill: safe / confirm / blocked
- Audit log: wer/was/warum (aus Router-Trace)

### 8.1 Autonomy)
 - Einen "Heatbeat" bauen, der das Modell wenn gewünscht aufweckt um aufgaben nach Crone Jobs zu erledigen.
 - Todo Liste für "Hearbeat" aufgaben zum Autonomen abarbeiten. (Ist leer oder bereits erledigt = NO_Reply)

## 9) LLM Bridge Panel (Gemini/Ollama)
- Persistent process status (running/respawn)
- Streaming output viewer
- Controls:
  - restart bridge
  - set bridge cwd
  - isolated bridge HOME optional
  - bridge-specific rules file (voice-only style)
- Latency breakdown: spawn_time, first_token_time, total_time
- Output shaping:
  - Speakable mode (1–3 Sätze, keine Codeblocks)
  - Full mode (nur UI/Log)

## 10) TTS / Voices Panel (Multi-Engine)
- Voice picker (Adapter-basierte Liste)
- Pronunciation lexicon editor (SSML/Rewrite rules)
- Test phrase runner (misst latency, RTF, first-chunk time)
- Barge-in responsiveness tests:
  - stop audio <100ms
  - cancel pipeline <250ms

## 11) Dev Context Panel ✅
Zweck: Inhalte für die nächste Voice-Anfrage automatisch als Kontext an LLM anhängen.

### A) Dev Context Buffer
- Multi-line editor (Monospace)
- Tabs: Error | Code | Paths | Terminal | Notes
- Syntax highlight optional
- Buttons: Clear | Copy | Attach Once | Persistent

### B) Auto-Attach Mechanismus (ohne Markdown-Bruch)
Wenn:
- neue Voice-Anfrage startet
- Dev Context nicht leer
- Router entscheidet “LLM/Chat” (nicht bei Hard Commands)

Dann:
- Event `dev_context_attached`
- Prompt Erweiterung als EIN Block:

(START_DEV_CONTEXT_BLOCK)
[DEV CONTEXT — UNTRUSTED]
<Inhalt>
[/DEV CONTEXT]
(END_DEV_CONTEXT_BLOCK)

### C) Regeln
- Toggle: Auto-Attach ON/OFF
- Mode:
  - Attach once and clear
  - Persistent until manually cleared
- Token-Kontrolle:
  - Token estimate anzeigen
  - Warnung bei Oversize
  - Optional: auto-truncate oldest lines

### D) Smart Mode (optional)
Wenn User sagt: “Analysiere diesen Fehler / Hier die logs / Fehler mitgegeben”
→ Auto-Attach wird forciert (auch wenn sonst OFF)

## 12) Debug / Replay Panel (SOTA)
- Liste der letzten N Sessions (“Runs”)
- Session klickbar: komplette Pipeline + timings + audio refs
- Export:
  - JSON trace im **Chrome Trace / Perfetto kompatiblen Format**
  - run manifest + artifact refs
- Regression:
  - replay golden set
  - diff view: timings + transcripts + router decisions

## 13) Runs / Artifacts Panel ✅
Jede Session schreibt ein **Run Manifest**:
- config snapshot (vollständig, versioned)
- model versions/hashes (STT/TTS/LLM)
- device IDs + DSP params
- artifact refs (audio_in, audio_out, traces) content-addressed (SHA256)
- retention policy (days, max runs)
- redaction status (on/off)

---

# 🔒 SECURITY & HARDENING (Pflicht)
- Skill allowlist + per-skill permissions: safe / confirm / blocked
- “Mute is hard”:
  - audio capture process-level wirklich aus
  - UI-State unmissverständlich
- Watchdog restart für Bridge/Engines ohne Crash-Loop
- Logs: redactable, debug mode getrennt, retention policy

---

# ⚡ PERFORMANCE TARGETS (Budgets, als P50/P95/P99)
- Wake → Listening: P95 <150ms
- End speech → STT final: P95 <900ms (profilabhängig)
- End speech → First TTS: P95 <1500ms (modellabhängig)
- Barge-in stop: audio <100ms / pipeline cancel <250ms
- Dev Context append overhead: <10ms

MCC muss live anzeigen:
- stage timings
- dropped frames (orb)
- underruns/overruns (audio)
- cpu/gpu usage (optional)

---

# 🪟 WAYLAND/COSMIC WINDOW CONTROL (Skill, realistisch)
Da Wayland programmatic window control einschränkt:
- Implementiere “Window Resize/Close/Move” als Skill über:
  - compositor shortcuts / portals / tool-based integration
- Commands:
  - “Fenster breiter/schmaler/höher/niedriger/schließen/minimieren”
  - step size konfigurierbar
  - “Resize mode” on/off

---

# 📦 DELIVERABLES (Output, am Ende)
1) Final System Design (1–2 Seiten)
   - Architecture diagram (Mermaid ok)
   - Data model (events/state)
   - UI layout + panel list
   - Defaults + Optionen + Empfehlung
2) Implementation Plan
   - Milestones (MVP → polish)
   - Risiken & Mitigations (Wayland, latency, jitter, echo)
3) Code Skeleton / Repo Layout
   - frontend/orb
   - frontend/mcc
   - backend/voice-engine
   - shared/types + schemas
   - docs/ (tuning, troubleshooting)
4) DoD + Acceptance Tests
   - golden tests list
   - latency/quality metrics
5) Quick Win Checklist (Immersion Boost)
6) AI Prompts
   - OneShot Implementierung + Testing + Validation
   - "New Feature-Upgrader" Master Prompt (Experte um neue Feauters in das laufende system zu bauen)
   - DoD + Acceptance Tests erstellen
   - End-to-End Testing
7) Tutorials (Frontend + Backend)
8) Documentation
   - API Documentation (REST/WebSocket)
   - User Guide (MCC/Orb)
   - Developer Guide (Engine)
9) CI/CD Plan
   - Regression replay goldens
   - Perf budgets gating
   - release/versioning strategy

---

# 🧾 OUTPUT STYLE
- Keine Floskeln.
- Alles konkret, implementierbar, mit Default-Werten.
- Wenn unsicher: 2 Optionen + Empfehlung.
- Annahmen klar als “ASSUMPTIONS” markieren.
- Zip mit Github Struktur und allen geforderten "DELIVERABLES".

---

## ASSUMPTIONS (wenn nicht anders angegeben)
- “0€” bedeutet: kostenlos nutzbar; 
- UI darf Web-Tech nutzen (Tauri/React) ODER Qt/QML; Architektur bleibt identisch.

BEGIN.
