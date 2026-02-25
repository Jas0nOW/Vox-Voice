# Tracing (Perfetto + Chrome Trace JSON + OTEL)

## Recommended v1
1) Emit **Chrome Trace JSON** events (Trace Event Format) per session.
2) Ensure B/E events are **perfectly nested** (no overlap) for Perfetto UI compatibility.
   - Perfetto explicitly notes overlapping B/E/X events are not supported in JSON traces.  
     Ref: https://perfetto.dev/docs/faq
3) Optionally, also create OTEL spans with the same `session_id` in attributes.

## Trace layout
- pid = 1 (voice-engine)
- tid per component track: capture, dsp, wake, vad, stt, router, llm, tts, skills, ui
- counters: rms_mic, rms_out, dropped_frames_orb, underruns, overruns

## Export
- `runs/<date>/<session_id>/trace.json` (Chrome JSON format)
- MCC loads the trace file and provides a “Open in Perfetto” convenience action.

References:
- Perfetto imports Trace Event Format: https://perfetto.dev/docs/getting-started/other-formats
- Trace Event Format spec: https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU/preview
- Perfetto TrackEvent (future upgrade): https://perfetto.dev/docs/instrumentation/track-events
