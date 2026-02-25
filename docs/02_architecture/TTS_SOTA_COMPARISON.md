# WANDA SOTA TTS Vergleich (Stand Feb 2026)

Dieses Dokument beschreibt die verfügbaren Profile und Einstellmöglichkeiten für die 5 SOTA TTS Engines.

## 🎙️ Deutsche Profile & Anpassbarkeit

### 1. Fish Audio (S1)
- **Profile:** "German Narrator" (Weiblich, reif, professionell).
- **Anpassung:** Über "Tone Markers" (Emotions-Tags im Text).
- **Cloning:** Ja (10-30 Sek. Referenz).

### 2. F5-TTS-German
- **Profile:** Keine (reines Cloning-Modell).
- **Anpassung:** Hängt zu 100% von der Referenz-Audiodatei ab.
- **Cloning:** Ja (Zwingend, ab 10 Sek. Audio).

### 3. Qwen3-TTS (Voice Design)
- **Profile:** Über 49 Presets für verschiedene Altersgruppen und Timbres.
- **Anpassung:** **Voice Design.** Erschaffung neuer Stimmen per Textbeschreibung (Prompting).
- **Cloning:** Ja (3 Sek. Quick-Clone).

### 4. Orpheus 3B
- **Profile:** "Jana", "Lena", "Anna" (Alle weiblich, deutsch, klar).
- **Anpassung:** Betonung und Emotion folgen dem Kontext des Textes (Speech-LLM).
- **Cloning:** Ja (Zero-shot).

### 5. XTTS v2
- **Profile:** "Marlene", "Vicky", "Hanna" (Deutsche Standard-Sprecherinnen).
- **Anpassung:** Stil-Transfer aus Referenz-Clips.
- **Cloning:** Ja (3-6 Sek. Audio).

---

## ⚙️ MCC Dashboard Integration (Planung)
Für jedes Modell wird im MCC ein Panel erstellt:
- **Preset-Wahl:** Dropdown der eingebauten Profile (z.B. Jana, Marlene).
- **Custom-Input:** Textfeld für Voice Design (Qwen3) oder Pfad zur Clone-Audiodatei (F5/XTTS).
- **Emotions-Regler:** Schieberegler für Modelle mit Tone Markers (Fish Audio).
