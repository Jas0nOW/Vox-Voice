# Prompt: OneShot Implementierung (Engine + WS + Trace + Runs)

You will implement the minimal working system in this repo:
- Python voice-engine (sim mode first)
- WebSocket event gateway (FastAPI)
- MCC web UI (vanilla HTML/JS) to view events & session timeline
- Run manifest + CAS blobs + Chrome Trace JSON export

Constraints:
- Every event includes session_id/event_id/schema_version.
- Export must load in Perfetto (no overlapping B/E).
- Provide CLI entrypoint `voice-engine`.

Output:
- PR-style diff summary
- How to run locally
- Acceptance test commands


Additional requirements:
- LLM bridge default is Gemini CLI (persistent process), selectable to Ollama.
- MCC top bar has quick toggles: Mute/Sleep/Stop + Fast/Thinking/Auto profile.
- Dev Context auto-attach block uses (START_DEV_CONTEXT_BLOCK)…(END_DEV_CONTEXT_BLOCK) markers.
