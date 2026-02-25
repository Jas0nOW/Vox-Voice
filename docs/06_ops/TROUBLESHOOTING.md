# Troubleshooting — WANDA Vox MCC

*Last updated: 2026-02-24*

---

## MCC not loading (blank page / no canvas)

**Check:** Is the dev server running?

```bash
cd frontend/mcc
python3 -m http.server 8080
# Open: http://localhost:8080
```

**Check:** Console errors in browser DevTools (F12)?
- `Cannot read properties of null` — wrong element ID in HTML vs app.js
- CORS error on WS → engine not running or port wrong

---

## Engine disconnected / WS not connecting

**Symptom:** Toast "Engine disconnected" immediately on load.

**Fix:** Start the voice engine backend:

```bash
cd backend/voice-engine
source .venv/bin/activate
voice-engine          # or: python -m voice_engine
```

Default WS ports:
- Events: `ws://127.0.0.1:7777/ws/events`
- Commands: `ws://127.0.0.1:7777/ws/command`

---

## "Warum restartet die Konsole?" (Why is the session restarting?)

The MCC logs restart reason in:
1. The **Session Status card** (Overview panel → "last restart reason")
2. The **Logs panel** — search for `[CSM] Restarting:`
3. The **Replay/Debug panel** — event `watchdog_restart`

### Restart reasons

| Reason | Cause | Fix |
|---|---|---|
| `initial_start` | Normal — first session start | — |
| `backend_switch` | User changed backend (Gemini ↔ Ollama) | Expected behavior |
| `settings_apply` | Settings applied with backend change | Expected behavior |
| `manual` | Force Restart button clicked | — |
| `crash` | Bridge process exited unexpectedly | Check Logs panel for bridge stderr |
| `watchdog` | Watchdog detected dead bridge | Check engine logs |

**Non-restart scenarios** (session preserved):
- Model/profile switch within same backend → always in-session, no restart

---

## Konsole restartet bei jedem Modell-Wechsel

**Cause:** You switched the **backend** (e.g., Gemini CLI → Ollama), not just the profile.

**Fix:** Use profile buttons (Fast/Reasoning/Auto) to switch within Gemini. Only switching from Gemini to Ollama requires a restart.

---

## Wie prüfe ich aktives Modell / Modus?

1. **Top bar status chips** — always visible:
   - `Model: fast` → current LLM profile
   - `Mode: CLI` → console mode
   - `Restart: —` → last restart reason

2. **Overview panel → Session Manager card** — full detail:
   - status, active model, profile, uptime, restart count

3. **Mode badge** (top bar, next to session chips):
   - Cyan = GEMINI mode
   - Purple = WINDOW INSERT mode

4. **Orb glow color:**
   - Cyan `#00F0FF` = GEMINI
   - Purple `#D600FF` = WINDOW_INSERT

---

## Neural canvas not animating / no particles

**Cause 1:** Browser does not support `requestAnimationFrame` or Canvas 2D (unlikely in 2026).

**Cause 2:** CSS `#neural-field` has wrong z-index (must be `z-index: 0`).

**Cause 3:** `pointer-events: none` missing on canvas — canvas may be blocking mouse events on UI elements.

**Fix:** Check browser console for JS errors in the IIFE `initNeuralField()`.

---

## Neural signals not firing

`window.neuralSignal(color)` is called after events. If signals don't appear:

1. Canvas init failed (check console)
2. `signalPairs` array empty because no particles are within 150px (window too small → particles spread far)
3. Performance: canvas may be in a tab that's not visible (rAF is throttled by browser)

---

## Orb click not toggling mode

1. Check `$('orb')` element exists in DOM (id=`orb`)
2. Check `$('orb').addEventListener` in bindUI() ran (look for errors before it)
3. Check: Is the mode badge updating? If badge updates but Orb glow doesn't → CSS `.window-insert-mode` class missing from styles.css

---

## Ctrl+M not working

1. Focus must be on the page (not in a browser address bar)
2. Check browser does not intercept Ctrl+M (e.g., some browser extensions)
3. Fallback: use the CLI/STT toggle buttons directly

---

## Perf Checks

### FPS (Neural canvas)

Open browser DevTools → Performance → Record 5s → check frame rate.
- Target: 60fps
- Common cause of drop: too many particles + too many connections
- Fix: reduce `PARTICLE_COUNT` to 60 or increase `CONNECT_DIST` threshold check (reduce from 150 to 120)

### Voice Pipeline Latency

**MCC shows P95 latency.** Check:
- Top bar: `P50 — / P95 — / P99 —` (populated after first LLM completion)
- Overview panel → Timeline: event sequence timing

**High P95 (>1500ms end-to-end)?**
1. Check STT model (large-v3 is slower; use turbo for speed)
2. Check LLM bridge: `first_token_time` in LLM Bridge panel
3. Check TTS: `first_chunk_latency` in TTS panel

### Barge-in responsiveness

Run from TTS panel: **"Run Barge-in Test"** button.
- Expected: audio stops within 100ms
- If >100ms: check sounddevice callback implementation in engine

### Audio underruns

Check Audio panel: underruns/overruns counters.
- Underruns: buffer too small or CPU overloaded during TTS generation
- Fix: increase `node.latency` in PipeWire config (must be multiple of 480 frames)

---

## Dev Context: tokens too high

- Warning appears at >2000 tokens
- Reduce: clear older tabs, use "Attach once" mode (clears after attach)
- Hard limit: LLM context window (Gemini: 1M tokens, Ollama models vary)

---

## Window Insert not showing

Window Insert panel only appears in Dev Context panel when Orb routing mode = `WINDOW_INSERT` (purple).
Click the Orb or Mode Badge to switch to WINDOW_INSERT mode.

---

## Chrome Trace export fails

- Requires at least one WS event received (replayEvents must be non-empty)
- Export button: Debug/Replay panel → "Export Chrome Trace JSON"
- View: drag file to `ui.perfetto.dev`
- Common issue: events with overlapping timestamps → Perfetto may not display correctly
  - Fix: all events use `ph:"X"` (complete events) with 1ms placeholder dur, not B/E pairs
