# TASKS - VOX-VOICE

Stand: 2026-02-26
Status: **CONSOLIDATION & STT FOCUS**

## Phase 0: System Cleanup & Consolidation (AKTUELL)
- [x] Stopp aller unkontrollierten Threading-Hacks ("v-talk").
- [x] Analyse der Kern-Architektur (`src/wandavoice/`).
- [ ] Zusammenführung der "Notizen-Insel" und der "Diktat-Insel" in den offiziellen Vox-Voice Core.
- [ ] Bereinigung der Orb-Kollisionen (Ein System, Ein UI).

## Phase 1: Perfektes STT Window-Insert (The Dictation Feature)
- [ ] Überarbeitung der `def dictate` in `main.py` auf ein sauberes, leck-freies State-Machine-Modell.
- [ ] **Sicheres Audio-Handling:** Audio wird nur bei gehaltener Taste/Toggle gesammelt, dann *einmalig* an Whisper gesendet. Kein Endlos-Streaming mehr in den VRAM.
- [ ] **Wayland-Safe Injection:** Nutzung der etablierten `insert.py` mit `wtype -m` und `pyperclip`-Fallback.
- [ ] **Strikte VAD-Filterung:** Nutzung von `SileroVAD` vor Whisper, um Rauschen (Halluzinationen wie Zahlen oder "Vielen Dank") zu verhindern.

## Phase 2: Notizen-Feature (The Second Island)
- [ ] Integration des Notizen-Workflows als separater Command (`vox note`) oder Modus innerhalb der gleichen Architektur.
- [ ] Speicherung in das definierte Markdown-Gedächtnis.

## Phase 3: The Supreme Assistant (Langzeitziel)
- [ ] Reaktivierung der LLM-Bridge (Gemini).
- [ ] Reaktivierung von TTS (Seraphina).
- [ ] Orchestrierung über AERIS.
