# WANDA Voice — Implementation Strategy (Architect Node)

*Date: 2026-02-25 · Status: Active · Environment: Pop!_OS + RTX 3070*

---

## I. MISSION STATEMENT
Transition **Vox-Voice** from an architecture-ready simulation/stub state into a high-performance, local-sovereign "Voice OS" leveraging the RTX 3070 for STT (Whisper Turbo) and TTS (F5-TTS).

---

## II. CORE DIRECTIVES (Project Specific)
1. **LOW-LATENCY FIRST**: Every decision must serve the P95 targets (Barge-in < 100ms, End-speech to TTS < 1500ms).
2. **VRAM MANAGEMENT**: Optimize for the 8GB VRAM limit. Use INT8/FP16 quantizations where possible.
3. **PIPEWIRE NATIVE**: No hacky audio routing. Use dedicated PipeWire nodes and monitors.
4. **TRACEABLE INTELLIGENCE**: Every interaction must generate a Perfetto-compatible trace for debugging and replay.

---

## III. SPRINT 1: "THE LOCAL SOVEREIGN" (The Audio Foundation)

### Goal: High-fidelity local STT and TTS running on GPU.

1. **[STT] Whisper Turbo Deployment**
   - Implement `faster-whisper` with `large-v3-turbo` model.
   - Use `compute_type="float16"` (optimized for RTX 3070).
   - Integrate `Silero VAD v5` with the existing HyperX Cloud III profile (threshold tuning).
   - **DoD**: Voice recognized in <500ms post-speech with >98% accuracy (German).

2. **[TTS] F5-TTS Integration**
   - Set up `F5-TTS` (local inference).
   - Select/Clone a high-quality German reference voice (replacing Seraphina/Azure).
   - Implement the "Streaming Chunk" bridge to reduce First-Token Latency.
   - **DoD**: Audio playback starts <800ms after LLM begins generating text.

3. **[DSP] PipeWire Cleanup**
   - Ensure `easyeffects_source` is the hard-coded default input.
   - Setup `module-echo-cancel` specifically for the HyperX Cloud III / Speaker loop.
   - **DoD**: No echo heard by the system during AI playback.

---

## IV. SPRINT 2: "THE VISUAL PULSE" (The Interface)

### Goal: The Orb UI as a native Wayland layer-shell overlay.

1. **[UI] Orb Surface (Python + GTK4)**
   - Implement `gtk4-layer-shell` integration.
   - Connect to the Backend Event Bus (WebSocket).
   - Implement the 60fps animation loop (Neural states: IDLE, LISTENING, THINKING, SPEAKING).
   - **DoD**: Orb is visible over all windows on Pop!_OS; reacts to mic levels with <50ms latency.

2. **[UI] MCC Neural Nexus Sync**
   - Connect the existing MCC React/Vite frontend to the live Backend.
   - Real-time visualization of the STT partials and TTS generation traces.

---

## V. SPRINT 3: "THE BARGE-IN" (The Interaction Loop)

### Goal: Seamless conversation with cancellation.

1. **[CORE] The Cancellation Token**
   - Wire `CancelToken` through STT, Router, LLM, and TTS adapters.
   - Implement the "Flush" logic for the audio ring buffer.
   - **DoD**: Speaking while the AI talks stops AI output instantly (<100ms).

---

## VI. NEXT STEPS (Immediate Actions)
1. Verify the Python environment for `F5-TTS` and `faster-whisper`.
2. Check `backend/voice-engine/engines/` for existing adapter stubs and refine them.
3. Start the implementation of the `F5-TTS` adapter.
