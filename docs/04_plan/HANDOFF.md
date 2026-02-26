# HANDOFF — STT WINDOW INJECTION (DICTATION)

## 🎯 STAND DER DINGE (Status Quo)
Das Feature "Diktat in das aktive Fenster" wurde nach 5 Stunden intensiver Fehlersuche (Wayland-Zahlen-Bug, Zombie-Prozesse, CUDA OOM) stabilisiert und in den Vox-Voice Kern integriert.

**ORT DER WAHRHEIT:** `/home/jannis/Schreibtisch/Work-OS/40_Products/Vox-Voice/src/wandavoice/main.py` -> `def dictate(...)`

## 🛠️ FUNKTIONALITÄT
- **Kommando:** `vox dictate --no-aura --no-console`
- **Trigger:** Rechte Strg-Taste (`Right Ctrl`).
- **Verhalten:** 
    1.  Hält man die Taste, nimmt Vox auf (VAD-gefiltert via Silero).
    2.  Beim Loslassen erfolgt eine 0,5s Verzögerung (um Modifier-Key-Konflikte zu vermeiden).
    3.  Transkription via `large-v3-turbo` (CUDA).
    4.  Injektion via `wtype` (Wayland-safe mit Modifier-Release `-m`).

## 🚩 WICHTIGE REPARATUREN (Lessons Learned)
1.  **Insel-Lösungen gelöscht:** Der Ordner `shared/` und alle `v-talk` Aliase wurden entfernt. Vox-Voice ist jetzt das **einzige** System.
2.  **Wayland-Fix:** `wtype` wurde um `-m ctrl_r` etc. erweitert, damit beim Tippen keine Escape-Zahlen (Zahlen-Bug) im Terminal erscheinen.
3.  **CUDA-Schutz:** Kein Streaming mehr in den VRAM. Audio wird gesammelt und *einmalig* verarbeitet.

## 🚀 NÄCHSTE SCHRITTE
- **Polish:** Finalisierung der VAD-Empfindlichkeit in `audio.py`.
- **Integration:** Das separat existierende `VOX-MIND` (Notizen) muss langfristig als Skill in die `main.py` integriert werden, um UI-Kollisionen (doppelte Orbs) zu vermeiden.

---
*Dokumentiert am 2026-02-26 | Ort: docs/04_plan/HANDOFF.md*
