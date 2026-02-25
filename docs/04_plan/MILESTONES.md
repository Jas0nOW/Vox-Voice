# Milestones (MVP → Polish)

## M0: Repo + schemas + simulation (1–2 days)
- event envelope + schemas
- ws gateway + MCC minimal UI
- run manifest + CAS + trace export
- simulated pipeline emitting events

## M1: Audio core + barge-in (3–7 days)
- PipeWire capture/playback
- ring buffer pre-roll (2–5s)
- cancel tokens wired through all stages
- stop playback <100ms + cancel <250ms acceptance tests

## M2: Wake/VAD/STT baseline (3–10 days)
- openWakeWord adapter
- VAD + endpoint profiles (command/chat)
- STT fast vs final
- confidence + timestamps + normalization rules

## M3: Orb overlay (2–5 days)
- gtk4-layer-shell orb surface
- 60fps renderer + dropped frame tracking
- audio-reactive animation

## M4: Replay/Regression (3–10 days)
- golden runs selection + index
- replay harness + diff views
- perf budget gating (P95)

## M5: Security/Skills hardening (ongoing)
- allowlist + permission matrix
- confirm flows
- dev-context untrusted enforcement

## M6: Polish (ongoing)
- latency dashboards
- device hot-swap
- AEC/NS/AGC tuning wizard
