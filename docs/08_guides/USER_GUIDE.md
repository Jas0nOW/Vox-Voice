# User Guide (MCC + Orb)

## Orb
- Shows current voice state (sleep/listen/think/speak/muted/error).
- Reacts to mic/output energy.
- Can be pinned per monitor (future setting).

## MCC
Overview:
- Shows current session_id, live state, key latencies.
Conversation:
- Partial + final transcript; copy/export; mark as golden.
Audio:
- mic/out levels; device selector; underrun/overrun counters (future).
DSP:
- AEC/NS/AGC toggles + test loop (future).
Dev Context:
- Paste logs/errors/paths; auto-attach to next LLM chat request.
Debug/Replay:
- Browse runs; export trace + manifest; replay goldens (future).

Safety:
- Skills may require confirmation depending on permission level.
- Dev context is treated as untrusted and never executed.
