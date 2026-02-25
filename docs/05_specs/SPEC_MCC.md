# MCC Spec (v1)

## Layout
Left nav:
- Overview, Conversation, Audio, DSP, Wake Word, VAD, STT, Router, Skills, LLM Bridge, TTS/Voices,
  Dev Context, Debug/Replay, Runs/Artifacts, Settings, Logs

Top bar:
- global state, session_id, latency P50/P95/P99, quick toggles (mute/sleep/stop/online-gate, fast/reasoning/auto for Gemini bridge)

## Required capabilities
- timeline (partial + final transcripts)
- live metrics panels (audio underruns/overruns, dropped frames, stage timings)
- run browser + export (trace + manifest)
- golden marking + regression replay trigger


## LLM bridge defaults
- Default backend: **Gemini CLI** (persistent process)
- Alternative: **Ollama** (local HTTP)
- Profiles exposed in UI: `fast` / `reasoning` / `auto`
