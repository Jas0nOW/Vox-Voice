# Handover Protocol — WANDA Voice

## Status Overview
- **Project Name:** WANDA Voice
- **Current Version:** 0.2.1
- **Status:** Development / MVP Phase
- **Last Update:** 2026-02-23

## Technical Context
- **Core Stack:** Python (Faster-Whisper, Edge-TTS, Silero VAD)
- **Architecture:** Transitioning from monolithic CLI to Event-Driven (Backend + Orb + MCC)
- **Backends:** PipeWire (Audio), FastAPI (WebSockets), Gemini CLI / Ollama (LLM)

## Active Tasks (Highlights)
- [ ] Stabilize integration between `voice-engine` and `frontend/mcc`.
- [ ] Finalize the "Orb" visual feedback loop.
- [ ] Implement full barge-in logic in the audio pipeline.

## Known Issues / Roadblocks
- Wayland specific constraints for global hotkeys (currently using evdev).
- Latency tuning for real-time interaction.

## Artifacts & Storage
- **Runs:** `backend/voice-engine/runs/`
- **CAS:** `backend/voice-engine/cas/`
- **Models:** `~/.wanda/models/`

## Instructions for next Instance
1. Verify the `.venv` consistency across `backend/` and root.
2. Review the `docs/02_architecture/` for the latest state machine definitions.
3. Check `docs/04_plan/TASKS.md` for the next implementation steps.
