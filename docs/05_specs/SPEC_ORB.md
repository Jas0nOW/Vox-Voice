# Orb Spec (v1)

## Surface & constraints
- Wayland **layer-shell** surface (OSD style).
- Default: non-click-through (safe).
- Optional click-through: keyboard_interactivity=none + empty input region.

Library recommendation:
- GTK4 + gtk4-layer-shell (supports GObject introspection).  
  Ref: https://github.com/wmww/gtk4-layer-shell

## States
SLEEPING, WAKE_DETECTED, LISTENING, THINKING, SPEAKING, MUTED, ERROR.

## Rendering budgets
- Target 60fps; count dropped frames; publish `orb_frame_stats` counters into tracing + MCC.

## Audio mapping
- mic RMS → wave amplitude (EWMA smoothed)
- tts RMS → glow/pulse
- state → motion profile

## Accessibility
- Reduced motion mode
- Not color-only: shape/tempo changes per state
