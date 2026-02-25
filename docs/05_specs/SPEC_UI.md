# UI Specification — WANDA MCC (Neural Nexus)

*Last updated: 2026-02-24 · Design: Neural Nexus*

---

## 1. Design System

### Color Tokens

| Token | Hex | Role |
|---|---|---|
| `--bg` | `#05050A` | Background (Void) |
| `--primary` | `#00F0FF` | Glow / Energy lines / Accent |
| `--secondary` | `#D600FF` | Depth / Secondary lines |
| `--particle` | `#FFFFFF` | Nodes / Highlight text |
| `--panel-bg` | `rgba(5,5,10,0.72)` | Glassmorphism panels |
| `--panel-border` | `rgba(0,240,255,0.14)` | Neural borders |

### Typography
- Body: `system-ui / -apple-system / Segoe UI`
- Mono: `ui-monospace / SFMono-Regular / Menlo`
- Base size: 13px / 1.5 line-height

### Glassmorphism Pattern (all panels)
```css
background: rgba(5, 5, 10, 0.72);
backdrop-filter: blur(18px) saturate(1.6);
border: 1px solid rgba(0, 240, 255, 0.14);
border-radius: 13px;
```

---

## 2. Neural Canvas (Background)

**File:** `frontend/mcc/canvas/neuralField.ts`

- Fixed fullscreen, z-index 0, `pointer-events: none`
- 100 bouncing particles (Neural Nexus)
- Distance-based line rendering: connect when `dist < 150px`
- Lines: gradient `primary → secondary`, alpha proportional to `(1 - dist/150)`
- `globalCompositeOperation = 'screen'` for additive glow
- Mouse gravity: particles within 200px pulled toward cursor
- Target: 60fps via `requestAnimationFrame`
- Degrade: trail alpha `#05050A40` (not full clear) → motion blur

### Signal Pulses (Neural Events)
Emitted via `window.neuralSignal(color)`. Animated dots travel along active connections.
- Animation: `t = 0 → 1` over 450-750ms, fade via `sin(t*π)`
- Trigger on: mode switch, orb click, LLM done, STT final, dev context attach

---

## 3. Orb / Oval

Position: Overview panel, centered in left card.

| Attribute | Value |
|---|---|
| Size | 130×86px (oval) |
| Border | 2px `--primary` |
| Glow | `0 0 36px rgba(0,240,255,0.65)` |
| Click action | Toggle routing mode |
| State: LISTENING | CSS animation `orb-breathe` 1.6s |
| State: SPEAKING | CSS animation `orb-pulse-fast` 0.8s |
| State: WINDOW_INSERT | Border + glow switch to `--secondary` |
| Hover | scale(1.05) + increased glow |

---

## 4. HUD / Toast System

- Position: `fixed; top: 56px; left: 50%; transform: translateX(-50%)`
- Queue-based (no simultaneous stacking)
- Auto-dismiss at 2200ms (configurable)
- Variants: `info` (cyan) · `warn` (gold) · `error` (red) · `secondary` (purple)
- Animation: `toast-in` cubic-bezier spring + `toast-out` fade

### Toast Trigger Map

| Event | Toast | Variant |
|---|---|---|
| Orb click: GEMINI | "⬡ Routing → Gemini" | info |
| Orb click: WINDOW_INSERT | "⬡ Routing → Window Insert" | secondary |
| Ctrl+M: CLI | "▸ CLI Mode (Console + LLM active)" | info |
| Ctrl+M: STT | "▸ Simple STT (pipeline only)" | info |
| Model switch | "Model → {name} (no restart)" | info |
| Backend switch | "Restarting session: backend_switch" | warn |
| cancel_done | "⊗ Pipeline cancelled" | warn |
| error_raised | "⚠ Error: {code} [{component}]" | error |
| Dev context attach | "⚡ Dev context attached (once)" | secondary |
| Engine connect | "Engine connected" | info |
| Engine disconnect | "Engine disconnected" | warn |

---

## 5. Mode Badge (Top Bar)

Persistent top-bar indicator of current routing mode. Also a click target for toggle.

| Mode | Text | Color | Dot |
|---|---|---|---|
| GEMINI | "GEMINI" | `#00F0FF` | Animated cyan pulse |
| WINDOW_INSERT | "WINDOW INSERT" | `#D600FF` | Static purple |

---

## 6. CLI/STT Toggle Switch

Pill-shaped toggle in topbar + Tinker panel. Shortcut: `Ctrl+M`.

- Active button: `rgba(0,240,255,0.12)` background, cyan border
- Inactive: transparent, `--muted` text
- Keyboard shortcut hint displayed next to toggle

---

## 7. Panel List + Key Interactions

| Panel | nav key | Key Features |
|---|---|---|
| Overview | overview | Orb, Session Manager status, Timeline, Last run |
| Conversation | conversation | User/AI timeline, Mark Golden, Export |
| Audio | audio | Device info, Ring buffer info |
| DSP | dsp | AEC/NS/AGC live, Mode switch (headset/speakers) |
| Wake Word | wake | FA/hour counter, PTT fallback |
| VAD | vad | Params, profile switch (command/chat), live "would end?" |
| STT | stt | Transcript, confidence, confusion tracking |
| Router | router | Last decision + reason, dev mode toggle |
| Skills | skills | Allowlist, audit log |
| LLM Bridge | llm | Backend/profile/pid, stream output, speakable/full toggle |
| TTS / Voices | tts | Engine, barge-in stats, test button |
| Dev Context | devctx | Multi-tab buffer, auto-attach, Window Insert (in WINDOW_INSERT mode) |
| Tinker MCC | tinker | CLI/STT toggle, model quick-switch, session manager controls |
| Debug / Replay | replay | Chrome trace export, event log (last 100) |
| Runs / Artifacts | runs | CAS path info, last manifest |
| Settings | settings | LLM + Voice preset apply |
| Logs | logs | Prepend log, clear, copy |

---

## 8. Interaction Feedback Rules

Every user interaction MUST produce:
1. **Ripple animation** — on button click (`ripple-wave` span injected)
2. **Toast/HUD** — brief, precise message
3. **Neural signal** — `window.neuralSignal(color)` call
4. **Timeline chip** — pushTimeline() event label
5. **Replay log entry** — logReplayEvent() for debug export

---

## 9. Accessibility

- `aria-label` on Orb (role="button")
- Reduced motion: remove `orb-breathe` / `orb-pulse-fast` if `prefers-reduced-motion`
- Keyboard navigation: Tab + Enter for all interactive elements
- Color is NOT the only mode indicator — always include text labels
