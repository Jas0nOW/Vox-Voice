# Flow Specifications — WANDA MCC

*Last updated: 2026-02-24*

---

## Flow 1: Model Switch

**Trigger:** Profile button click (Fast / Reasoning / Auto) or model select

```
User clicks profile button
  │
  ├─► [Same backend?]
  │     YES ─► CSM.switchModel(profile)
  │              ├─► config updated in-session
  │              ├─► no restart
  │              ├─► emit: config_updated
  │              ├─► toast: "Model → {profile} (no restart)"
  │              └─► neuralSignal(#00F0FF)
  │
  └─── NO (backend switch) ─► CSM.ensureRunning({backend: newBackend})
                                 ├─► _restart('backend_switch')
                                 ├─► stop existing bridge (SIGTERM → SIGKILL)
                                 ├─► start new bridge with new command
                                 ├─► emit: restarting → started
                                 ├─► toast: "Restarting: backend_switch" (warn)
                                 └─► neuralSignal(#D600FF)
```

**Invariant:** Model switch within same backend never triggers a restart.

---

## Flow 2: CLI ↔ STT Mode Switch

**Trigger:** Toggle button click OR `Ctrl+M` keyboard shortcut

```
User presses Ctrl+M (or clicks toggle)
  │
  ├─► setConsoleMode('cli' | 'simple_stt')
  │
  ├─► [cli selected]
  │     ├─► send WS cmd: set_console_mode {mode: 'cli'}
  │     ├─► engine enables: console + llm-routing + tts
  │     ├─► toggle buttons updated (active-toggle class)
  │     ├─► status chip: "CLI"
  │     ├─► toast: "▸ CLI Mode (Console + LLM active)"
  │     └─► neuralSignal(#00F0FF)
  │
  └─► [simple_stt selected]
        ├─► send WS cmd: set_console_mode {mode: 'simple_stt'}
        ├─► engine enables: stt-pipeline only (no LLM, no TTS)
        ├─► toggle buttons updated
        ├─► status chip: "STT"
        ├─► toast: "▸ Simple STT (pipeline only)"
        └─► neuralSignal(#00F0FF)
```

**Performance:** Mode switch must not restart audio capture (PipeWire capture stays up).

---

## Flow 3: Orb Routing Toggle (Gemini ↔ Window Insert)

**Trigger:** Click on Orb/Oval OR Mode Badge in topbar

```
User clicks Orb
  │
  ├─► state.routingMode toggles: GEMINI → WINDOW_INSERT (or reverse)
  │
  ├─► [→ GEMINI]
  │     ├─► modeBadge: "GEMINI" (cyan, pulse dot)
  │     ├─► orb: remove window-insert-mode class
  │     ├─► orb glow: --primary (#00F0FF)
  │     ├─► orbModeLbl: "⬡ GEMINI MODE"
  │     ├─► Window Insert panel: hidden
  │     ├─► toast: "⬡ Routing → Gemini" (info)
  │     └─► neuralSignal(#00F0FF)
  │
  └─► [→ WINDOW_INSERT]
        ├─► modeBadge: "WINDOW INSERT" (purple)
        ├─► orb: add window-insert-mode class
        ├─► orb glow: --secondary (#D600FF)
        ├─► orbModeLbl: "⬡ WINDOW INSERT"
        ├─► Window Insert panel: visible (in Dev Context panel)
        ├─► toast: "⬡ Routing → Window Insert" (secondary)
        └─► neuralSignal(#D600FF)

Next voice request in WINDOW_INSERT mode:
  stt_final → append transcript to windowInsertText buffer
  (no LLM invocation, no TTS response)
```

**Visibility rule:** Mode must be unmissable at all times:
- Orb glow color
- Mode badge in topbar
- `orbModeLbl` text below Orb

---

## Flow 4: Dev Context Attach

**Trigger:** "⚡ Attach" button click OR auto-attach on next voice request

```
User clicks "⚡ Attach"
  │
  ├─► validate: text not empty
  │     EMPTY → toast: "Dev context: nothing to attach" (warn)
  │
  ├─► send WS cmd: set_dev_context {text, auto_attach: true, mode: 'once'}
  │
  ├─► engine receives → wraps buffer:
  │     (START_DEV_CONTEXT_BLOCK)
  │     [DEV CONTEXT — UNTRUSTED]
  │     {content}
  │     [/DEV CONTEXT]
  │     (END_DEV_CONTEXT_BLOCK)
  │
  ├─► engine emits: dev_context_attached event
  │
  ├─► MCC receives event:
  │     ├─► toast: "⚡ Dev context attached (once)" (secondary)
  │     ├─► neuralSignal(#D600FF)
  │     └─► pushTimeline("dev_ctx_attached")
  │
  └─► if mode === 'once': clear text buffer after attach
```

**Auto-attach flow (on next voice request):**
```
stt_final received by engine
  │
  ├─► dev_context.auto_attach === true AND text not empty?
  │     YES → prepend dev_context block to LLM prompt
  │           emit: dev_context_attached
  │           if mode === 'once': clear buffer
  │
  └─► NO → normal LLM prompt (no context block)
```

**Token warning:** >2000 tokens → amber warning. Auto-truncate oldest lines if configured.

---

## Flow 5: Barge-in (Hard Requirement)

```
User speaks while WANDA is SPEAKING
  │
  ├─► VAD detects voice → vad_start event
  │
  ├─► cancel_request emitted immediately (reason: barge_in)
  │
  ├─► TTS playback stop: <100ms target
  │     sounddevice: sd.CallbackStop in audio callback
  │
  ├─► Pipeline cancel: <250ms target
  │     CancelToken set → all awaiting stages abort
  │     TTS chunk queue drained
  │     LLM stream cancelled
  │
  ├─► cancel_done emitted → MCC shows "⊗ Pipeline cancelled" toast
  │
  └─► State → LISTENING (new voice session begins)
```
