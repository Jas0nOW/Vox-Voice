# DoD + Acceptance Tests

## Hard timing (measured)
- Barge-in stop playback: **<100ms** (P95)
- Pipeline cancel complete: **<250ms** (P95)
- Wake → Listening: **<150ms** (P95)

## Functional
- Every event includes session_id + event_id + ts.
- All pipeline stages emit start/end spans + errors.
- Run manifest written for every session.
- Replay mode can re-run golden sets and produce diffs.

## Safety
- Skill invocation requires allowlist + permission decision logged.
- Dev context attaches only in explicit untrusted block.
- Mute closes capture stream (not just UI state).

## Observability
- Export trace.json and open in Perfetto without parse errors.
- No overlapping B/E events in JSON trace (nesting compliant).
