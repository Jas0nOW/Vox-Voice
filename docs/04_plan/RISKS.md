# Risks & Mitigations

## Wayland / COSMIC protocol support
Risk: compositor differences (layer-shell, input semantics).
Mitigation: rely on wlr-layer-shell via gtk4-layer-shell; fall back to normal window if unavailable; keep Orb optional.

## Realtime constraints in Python
Risk: jitter, GC pauses.
Mitigation: move hard realtime to PipeWire graph; keep Python orchestrator; consider Rust for capture/playback supervisor if needed.

## AEC quality varies by device
Risk: bad echo cancellation in speaker mode.
Mitigation: start with PipeWire echo-cancel (WebRTC); add in-engine WebRTC AP for per-session tuning; provide AEC test loop.

## Trace JSON nesting
Risk: Perfetto import issues if spans overlap on same track.
Mitigation: strict nesting per tid; use separate tracks per concurrent activity; add trace validation in CI.

## Security boundaries
Risk: dev context or LLM outputs triggering unsafe actions.
Mitigation: allowlist-only skills; confirm flows; untrusted dev context; audit logs + dry-run mode.
