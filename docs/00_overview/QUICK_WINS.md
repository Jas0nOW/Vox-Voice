# Quick Win Checklist (Immersion Boost)

Orb:
- 60fps redraw loop + dropped-frame counter in MCC
- EWMA smoothing for mic/out RMS (no jitter)
- Distinct state cues (glyphs/tempo) — not color-only
- Ambient idle mode (very low energy) + reduced motion toggle
- Short earcons (optional) for WAKE_DETECTED / ERROR / MUTE

Audio:
- Pre-roll ring buffer enabled (2–5s) so the first word is never clipped
- Calibrate noise floor + show “first-word drop” counter in MCC
- Separate capture and playback threads/tasks; never block capture

Observability:
- One trace per session (Chrome Trace JSON) + run manifest written every time
- Export button: manifest + trace + transcripts

Debug:
- “Mark as Golden” workflow + one-click replay
- Diff view (router decisions + transcript + timings)
