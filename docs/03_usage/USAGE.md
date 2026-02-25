
# Usage

## Standard (Voice → stdout)
```bash
wanda voice --mic --target stdout
```
Trigger ist `Right Ctrl` (Mic Toggle).

## Orb UI (Always-on-top, draggable)
```bash
wanda voice --mic --orb
```

- **Drag**: Linksklick halten → Orb verschieben.
- **Linksklick**: Briefing / Status.
- **Rechtsklick**: Menü (Briefing, Stop, Pause/Resume, Quit)

Hinweis: Unter **Wayland** (z. B. COSMIC) kann "always on top" bzw. Hotkey/Injection je nach Compositor eingeschränkt sein.

## Dictation (Voice → Insert Clipboard)
```bash
wanda voice --mic --target insert --insert clipboard
```

## LLM Route (Gemini)
```bash
wanda voice --mic --target cli:gemini --tts azure
```

## LLM Route (Ollama lokal)
```bash
wanda voice --mic --target cli:ollama --ollama-model llama3.1
```

## Ollama TTS (experimentell)
```bash
wanda voice --mic --target cli:ollama --tts ollama
```

## Safe Mode
```bash
wanda voice --mic --safe
```

Im `--safe` Mode werden Insert/Clipboard/Exec/TTS **hart deaktiviert**. Output geht nur nach stdout + Audit.

## UI / Konfiguration
```bash
wanda voice ui
wanda voice configure
wanda voice permissions
wanda voice config --get voice.routing.target
wanda voice config --set voice.tts.azure.voice de-DE-SeraphinaNeural
wanda voice config --set voice.ui.orb_enabled true
wanda voice config --set voice.ui.preview_enabled true
wanda help
wanda voice help
```

## Improve Modes
```bash
wanda voice --mic --improve off
wanda voice --mic --improve basic   # default
wanda voice --mic --improve prompt  # professional prompt for cli targets
```

## Voice Control
Diese Kommandos werden aus dem transkribierten Text erkannt (DE/EN).  
**Robustheit/Anti-False-Trigger:**  
- Kommandos ohne "Wanda" werden nur erkannt, wenn es **kurz** und **command-like** ist (wenige Wörter).  
- Kritische Kommandos (Exit) werden ohne "Wanda" nur als **Standalone** erkannt.  
- Wenn "Wanda" irgendwo im Satz vorkommt, werden Kommandos auch am Satzende erkannt (z. B. „… Wanda“), ohne dass der Rest als Diktat "eingefügt" wird.

### Wake / Aktivieren
- „Hey Wanda“, „Hallo Wanda“, „Ok Wanda“, „Wanda“
- „Guten Morgen Wanda“ → macht direkt ein Briefing

### Briefing / Status / Neues
- „Briefing“, „Status“, „Status Update“, „Lagebericht“
- „Was gibt es neues“ / „Wanda was gibt es neues“
- „Übersicht“ / „Status Übersicht“

### Wiedergabe / Vorlesen
- „Wiederholen“ / „Noch mal“ (wiederholt die letzte Antwort)
- „Kannst du mir das vorlesen“ / „Vorlesen“ (liest bevorzugt den letzten SHOW-Text vor)

### Pause / Schlaf
- „Pause“ (Idle/Leerlauf)
- „Gute Nacht Wanda“ (wie Pause)

### Stop / Abbrechen
- „Stop“, „Stopp“, „Halt“, „Abbrechen“, „Unterbrechen“ (stoppt TTS sofort)

### Exit / Beenden (kurz & Jarvis-style)
- „Ausschalten“, „Abschalten“, „Runterfahren“, „Herunterfahren“
- „Schließe dich“, „Das war es für heute“, „Beenden“, „Quit“, „Exit“

**Hinweis:** „wander“ wird im Greeting-Kontext als **ambiguous** erkannt, um Fehl-Trigger zu vermeiden („Meintest du Wanda?“).
