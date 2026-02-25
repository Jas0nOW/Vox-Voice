
# WANDA Voice System (wandavoice) — MVP-Plan (extrahiert)

## 0) Zielbild (Voice-Only MVP) 🎙️
Wir bauen WANDA als MVP, indem wir **nur das Voice-System** liefern: ein **Voice Gateway**, das Sprache zuverlässig zu **Text** macht, optional Text **verbessert**, dann **Text einfügt** (Active Window) oder **routet** (stdout / Datei / externe CLI), und optional **TTS** ausgibt.

**Primärer Nutzen:** „Ich spreche → Text landet dort, wo ich gerade tippe (IDE/Terminal/Browser)“  
**Sekundärer Nutzen:** „Ich spreche → Text geht an eine Engine/CLI → Antwort wird gesprochen“

---

## 1) Scope / Nicht-Scope

### 1.1 In Scope (MVP) ✅
- **Audio Capture**
  - Push-to-talk (Hotkey oder „Press Enter to record“ als minimaler Start)
  - stabile Aufnahme (optional Noise Gate / AGC als spätere Option)
- **VAD (Silence Detection)**
  - optionaler Auto-Stop bei Stille (toggle)
- **STT (Speech-to-Text)**
  - provider-agnostisch über Adapter
  - lokal oder cloud (MVP: 1 Default + 1 Alternative möglich)
- **Prompt-Improver (optional)**
  - Voice-Text kann vor Output verbessert werden (on/off + Modus)
- **Target Routing (MVP: mindestens 2 Ziele)**
  - **Active-Window Text Insert** (wichtigster Pfad)
  - **stdout** (Fallback / Debug / Pipe)
  - optional: externe CLI (Gemini/Codex/Claude), wenn User es aktiviert
- **TTS (optional, aber für „Jarvis feel“ empfohlen)**
  - mindestens 1 Engine (z. B. Azure/Microsoft Voices)
  - Stop/Cancel während TTS (Keyword oder Hotkey)
- **Minimal UI/UX**
  - CLI first
  - optional: „Voice-Ball“ (Siri-Orb) als Mini-GUI später im MVP-Zyklus

### 1.2 Nicht-Scope (Voice-Only MVP) ❌
- Kein `wandacode`/`wanda` Orchestrator (nur **Routing-Stubs** als Ziele)
- Kein Autonomy/Heartbeat/Task-System
- Kein Marketplace/Plugin-Ökosystem (nur interne Adapter-Interfaces)

---

## 2) CLI-Produktform

### 2.1 Hauptbefehl
- `wanda voice` (Alias: `wandavoice`)

### 2.2 Empfohlene Subcommands / Flags (MVP-freundlich)
- `wanda voice --mic`
  - startet Push-to-talk + VAD + STT
- `wanda voice --text "<input>"`
  - behandelt Text wie STT-Ergebnis (Test / Automationen)
- Wichtige Flags:
  - `--vad on|off`
  - `--stt <provider>` (z. B. `local_whisper`, `cloud_*`)
  - `--lang de|en|auto`
  - `--insert active|clipboard|off`
  - `--target insert|stdout|cli:<name>`
  - `--tts azure|none|auto`
  - `--device <index>`
  - `--reset` (Session/History leeren)
  - `--safe` (kein Insert/Clipboard/Exec; nur stdout)

---

## 3) User Flows (MVP)

### Flow A — Dictation to Active Window (Core) 🧠
1) User startet `wanda voice --mic`
2) User spricht
3) VAD stoppt oder User stoppt manuell
4) STT transkribiert
5) Optional: Prompt-Improver
6) InsertAdapter schreibt Text in aktives Fenster (oder via Clipboard-Fallback)

### Flow B — Voice to CLI Engine (optional) 🤖
1) Voice → STT → optional Improve
2) Router sendet Text an externe CLI (z. B. „gemini“) via subprocess/stdio
3) Ergebnis wird:
   - optional gesprochen (TTS)
   - optional zusätzlich als Text eingefügt oder nach stdout geschrieben

### Flow C — „Safe Mode“ (Debug / Datenschutz)
- Kein Insert, kein Clipboard, kein Exec
- Nur STT → stdout (plus lokale Logs)

---

## 4) Architektur (Voice Gateway)

### 4.1 Module (MVP)
- **audio/**
  - Aufnahme, Device-Auswahl, Frames/Chunks
  - optional: Level-Meter (später)
- **vad/**
  - Silence detection (Schwellwerte + ms-Window)
- **stt/**
  - `STTAdapter` Interface
  - Implementierung(en): mindestens 1 Default
- **improve/**
  - optionaler „Prompt-Improver“
  - Modus: `off | clean | rewrite | command`
- **router/**
  - entscheidet Ziel(e) anhand Config/Flags
- **insert/**
  - `InsertAdapter` Interface
  - OS-spezifische Implementierung (siehe 5)
- **tts/**
  - `TTSAdapter` Interface
  - mind. 1 Engine + cancel/stop
- **session/**
  - optional: History/Context (für CLI-engine chat)
- **config/**
  - lokale Config + env keys + profile „voice-only“
- **logging/audit/**
  - Events: record_start/stop, stt_done, route_target, insert_done, tts_start/stop, errors

### 4.2 Adapter-Interfaces (Contracts)
- `STTAdapter`
  - `transcribe(audio_bytes, lang, options) -> text`
  - optional: streaming später
- `TTSAdapter`
  - `speak(text, voice, speed) -> None`
  - `stop() -> None`
- `InsertAdapter`
  - `insert_text(text, mode=typing|clipboard) -> None`
  - `healthcheck_permissions() -> status`

---

## 5) Text-Insert Strategie pro OS (MVP)

### Ziel
**Active-Window Text Insert** muss robust sein. MVP kann mit „1 OS Gold-Standard“ starten, andere als „best-effort“.

### Insert Modes (Reihenfolge)
1) **Typing Injection** (simulierte Tastatur)
2) **Clipboard Paste** (copy → paste) als Fallback
3) **Off** (safe/debug)

### OS-Hooks (Plan)
- **Windows**
  - bevorzugt: SendInput / UI Automation (je nach Tech-Stack)
  - Hinweis: benötigte Rechte/Focus-Constraints dokumentieren
- **macOS**
  - Accessibility APIs (Permissions sind kritisch)
- **Linux**
  - X11: xdotool-ähnlich / native
  - Wayland: wtype/portals; Einschränkungen sauber dokumentieren

**MVP-Entscheidung:** 1 OS als „Gold“ vollständig, die anderen zunächst als Fallback + Dokumentation.

---

## 6) TTS Optionen (MVP)
- Option A: **Microsoft/Azure Voices** (z. B. „Seraphina“ als wählbare Stimme)
- Option B: Alternative Engine (z. B. „Qwen-TTS“) als Add-on
- Offline-Fallback: nur wenn realistisch stabil (sonst später)

**MVP-Anforderung:** Stop/Cancel während TTS (Hotkey oder Keywords wie „Stop/Stopp/Halt“).

---

## 7) Config & Permissions (Voice-Only, minimal aber sauber) 🔐

### 7.1 Config (Beispiel)
- `~/.wanda/config.yaml` oder XDG/AppData
- Abschnitt `voice:`:
  - stt provider + model
  - lang
  - vad on/off + thresholds
  - insert mode + allowed scopes
  - tts provider + voice
  - target routing defaults
  - privacy level (z. B. „no_cloud“)

### 7.2 Permissions / Guardrails (MVP)
- Scopes:
  - `audio_record`
  - `clipboard_write`
  - `window_inject`
  - `exec_external_cli`
  - `network` (nur wenn cloud-stt/tts)
- Default: **ask-first / safe**
- Audit Log: „was wurde wohin geroutet“ (ohne sensible Inhalte, wenn Privacy-Level das verlangt)

---

## 8) Milestones (nur Voice)

### V0 — Repo/Package Skeleton (Day-1)
- CLI Entry (`wanda voice`)
- Config Laden + Default-Profil „voice-only“
- Logging/Audit minimal
- Adapter Interfaces als Stubs

### V1 — Wandavoice MVP ✅
- Push-to-talk + Aufnahme
- VAD toggle
- STT → Text
- Routing:
  - Active Window Insert (mind. 1 OS „Gold“)
  - stdout fallback
- TTS optional (mind. 1 Provider)
- Minimal UI: CLI stabil + klare States (idle/recording/thinking/speaking/off)

### V1.1 — UX Hardening
- Device selection
- Cancel/Stop zuverlässig
- Error recovery (STT fail → fallback)
- Config Wizard minimal (CLI prompts)

### V1.2 — Mini-GUI „Voice Ball“ (optional im MVP-Zyklus) ✨
- Zustände: Recording / Thinking / Speaking / Idle / Off
- Toggle: VAD, Improve, Target, Device
- Muss ohne GUI weiter funktionieren (CLI bleibt first-class)

---

## 9) Definition of Done (Voice-Only MVP)
Erfolgreich, wenn:
- `wanda voice --mic` zuverlässig: **STT → Insert → (optional TTS)**
- Insert funktioniert stabil im Gold-OS, und Fallbacks sind dokumentiert
- `--safe` verhindert Insert/Clipboard/Exec sicher
- Logs/Audit sind nachvollziehbar
- Provider/Adapter sind austauschbar (keine Hardcodings)

---

## 10) Offene Entscheidungen (Voice-relevant)
1) **Gold-Standard OS** für MVP zuerst?
2) Default Voice-Stack:
   - STT: lokal vs cloud (Kosten/Latency/Privacy)
   - VAD: Parameter/Lib
   - TTS: Azure/Microsoft vs Alternative
3) Text-Insert: bevorzugter technischer Weg pro OS (Typing vs Clipboard als Default)
4) Prompt-Improver: minimaler Nutzen vs Latenz (Default off?)

---

## 11) (Optional) Mapping zu vorhandenem `voice_mvp/` Ordner
Falls bereits ein Voice-CLI existiert, passt es typischerweise so:
- `audio.py`  → audio capture
- `stt.py`    → STTAdapter + Default-Impl
- `tts.py`    → TTSAdapter + Default-Impl + stop
- `llm.py`    → Prompt-Improver / externe CLI routing
- `session.py`→ History/Context (Flow B)
- `config.py` → voice config + env
- `main.py` / `__main__.py` → CLI entry (`wanda voice` Alignment)
"""