# WANDA Voice Task List

*Updated: 2026-02-24 · Version: 2.0*

---

## ✅ Completed

### 🎙️ TTS Integration
- [x] SOTA Research & Model Selection
- [x] Multi-Engine Adapter System (Base Class)
- [x] Sample Generation: Fish Audio S1, Orpheus 3B, Qwen3-TTS
- [x] F5-TTS Integration + reference audio selection

### ⚙️ Audio Pipeline
- [x] arecord System Stream (EasyEffects fix)
- [x] Silero VAD v5 Implementation
- [x] Whisper large-v3-turbo / large-v3 selection

### 🎮 MCC v2 — Neural Nexus Design
- [x] Neural canvas (100 particles, distance-lines, screen composite, mouse gravity)
- [x] Neural signal pulses (emit on events)
- [x] Toast/HUD system (queue, variants, auto-dismiss)
- [x] ConsoleSessionManager (idempotent, model switch no-restart)
- [x] RoutingMode toggle — Gemini ↔ Window Insert
- [x] ConsoleMode toggle — CLI ↔ Simple STT (+ Ctrl+M)
- [x] Orb/Oval with state animations (LISTENING/SPEAKING)
- [x] Mode badge + session status chips in topbar
- [x] Window Insert panel (visible in WINDOW_INSERT mode)
- [x] Tinker MCC panel (model quick-switch, session manager controls)
- [x] Ripple effect on all buttons
- [x] Chrome Trace JSON export (Perfetto-compatible)
- [x] Conversation monitor (user/AI timeline, partial/final, mark golden)

### 📚 Architecture + Docs
- [x] ARCH.md (CSM rules + state machine + routing mode)
- [x] SPEC_UI.md (Neural design system + panel list + feedback rules)
- [x] SPEC_FLOWS.md (5 complete flow diagrams)
- [x] shared/state/types.ts (all types)
- [x] shared/state/store.ts (observable store + React adapter)
- [x] backend/console/ConsoleSessionManager.ts (full TypeScript)
- [x] frontend/mcc/canvas/neuralField.ts (TypeScript renderer)
- [x] React component stubs: OrbNeural, TinkerPanel, DevContextPanel

---

## 🔲 MVP — In Progress / Next

### MCC New Feature-Upgrader (see prompts/tasks/FEATURE_UPGRADES.md)
1. [x] **Pre-roll ring buffer** (2–5s) saved to artifacts
2. [x] **CancelToken** wired through all stages + barge-in stop <100ms
3. [ ] **openWakeWord adapter** + false-positive counter per hour
4. [x] **VAD profiles** (command/chat) with live prediction preview event
5. [ ] **STT fast vs final** + timestamps + confusion tracking
6. [ ] **DSP panel instrumentation** (`dsp_state` events) + test loop harness
7. [ ] **Skill allowlist** + permission/confirm flows + audit log
8. [ ] **Golden runs + replay harness** + diff view for router decisions
9. [ ] **Perf budget gating** (P95 thresholds) with regression report

### 🌀 Orb (ui-orb Python)
- [ ] layer-shell integration (Wayland / COSMIC) via gtk4-layer-shell
- [ ] 60fps animation loop with orb state → visual transitions
- [ ] Audio-reactive: mic_level → wave amplitude (RMS), tts_level → glow
- [ ] Multi-monitor support (`LayerShell.set_monitor`)

### 📡 Backend Voice Engine
- [ ] PipeWire AEC: `module-echo-cancel` webrtc + `monitor.mode=true`
- [ ] openWakeWord ONNX adapter (80ms frames, 16kHz, threshold 0.5)
- [ ] Barge-in: `sd.CallbackStop` + CancelToken <100ms audio / <250ms pipeline
- [ ] Run manifest + CAS (hashfs, SHA256)
- [ ] Perfetto trace emission (ph:"X", ts μs)

---

## 🔒 DoD Per Feature

Each new feature from FEATURE_UPGRADES.md must:
- [ ] Implement feature in separate commit
- [ ] Update docs (relevant spec + ARCH if needed)
- [ ] Add acceptance test (see docs/04_plan/ACCEPTANCE_TESTS.md)
- [ ] Update MCC panel (even if minimal)

---

## ⚡ Performance Budgets (P95)

| Stage | Target |
|---|---|
| Wake → Listening | <150ms |
| End speech → STT final | <900ms |
| End speech → First TTS | <1500ms |
| Barge-in audio stop | <100ms |
| Barge-in pipeline cancel | <250ms |
| Dev context attach overhead | <10ms |

---

## 🏗️ Optional / Polish

- [ ] XTTS v2 (Marlene) — Optional TTS engine
- [ ] React migration for MCC (Vite + React, components already scaffolded)
- [ ] CI/CD: regression replay goldens + perf budget gating
- [ ] OTEL spans with `otel-file-exporter` on backend
- [ ] Heartbeat / Cron autonomous task loop (Skills panel)
