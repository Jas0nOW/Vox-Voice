# Prompt: New Feature-Upgrader

Implement in separate commits (one feature per commit):
1) Pre-roll ring buffer (2–5s) saved to artifacts
2) CancelToken wired through all stages + barge-in stop <100ms
3) openWakeWord adapter + false-positive counter per hour
4) VAD profiles (command/chat) with live prediction preview event
5) STT fast vs final + timestamps + confusion tracking
6) DSP panel instrumentation (`dsp_state` events) + test loop harness
7) Skill allowlist + permission/confirm flows + audit log
8) Golden runs + replay harness + diff view for router decisions
9) Perf budget gating (P95 thresholds) with regression report

For each:
- update docs
- add acceptance tests
- update MCC panel (even if minimal)
