# Projekt: WANDA Voice System

*Last updated: 2026-02-24 · Version: 2.0*

## Ziel
Ein zentrales **Voice OS**, das als immersive Brücke zwischen dem Nutzer und dem System/AIs dient.

## MCC — Mission Control Center (Neural Nexus)

Das MCC ist die Control-Plane des Voice OS. Browser-basiert (vanilla HTML/JS/CSS), Neural Nexus Design.

**Design:** Neural Nexus — `#05050A` / `#00F0FF` / `#D600FF` / `#FFFFFF`
**Canvas:** 100 Particles, Distance-Line Rendering, `globalCompositeOperation='screen'`, Mouse-Gravity, 60fps
**Signal Pulses:** Animierte Neural-Signale entlang aktiver Verbindungen bei jedem Event

### Haupt-Modi

| Feature | Beschreibung |
|---|---|
| **Orb/Oval** | Zentrales immersives Visual — click toggles routing mode |
| **Routing Mode** | GEMINI (→ LLM) ↔ WINDOW_INSERT (→ Dev Context Buffer) |
| **Console Mode** | CLI (voll) ↔ Simple STT (nur Transkription) — Ctrl+M |
| **ConsoleSessionManager** | Idempotentes Session-Management — Model-Switch ohne Neustart |
| **HUD/Toast** | Queue-basiertes Feedback bei jeder Interaktion |
| **Chrome Trace Export** | Perfetto-kompatibel für Pipeline-Analyse |

### Panels

Overview · Conversation · Audio · DSP · Wake Word · VAD · STT · Router · Skills
LLM Bridge · TTS/Voices · Dev Context · **Tinker MCC** · Debug/Replay · Runs · Settings · Logs

## SOTA Local TTS Strategie (Februar 2026)
WANDA nutzt ein isoliertes Multi-Engine System für maximale Stabilität und Qualität.

### Das SOTA-Quintett (Umschaltbar im MCC)
1.  **XTTS v2:** (Stabilisierung via Python 3.10 läuft).
2.  **Fish Audio S1:** (In Vorbereitung).
3.  **Qwen3-TTS:** (Voice Design Engine).
4.  **Orpheus 3B:** (Speech-LLM für intelligente Interaktion).
5.  **F5-TTS:** (Pending: Auswahl eines deutsches Samples).

## Workspace Hygiene
- Modelle werden unter `~/.wanda/models/` zentral gelagert.
- Jede Engine läuft in einer isolierten Umgebung unter `engines/<name>`.
- Redundante Daten und failed Venvs werden sofort bereinigt.
