
# Gemini Prompt: Install + Test WANDA Voice System

Du bist ein pragmatischer Linux CLI Engineer. Arbeite strikt Schritt-für-Schritt, ohne riskante Befehle.

## Ziel
Projekt liegt hier:
`/home/jannis/Schreibtisch/Work-OS/40_Products/WANDA/voice_mvp/`

Bitte:
1) System-Dependencies installieren (Pop!_OS / Ubuntu)
2) Python venv erstellen
3) Package installieren (editable)
4) Tests laufen lassen
5) Smoke Tests ausführen:
   - devices listen
   - --text mode stdout
   - mic stdout
   - mic insert clipboard (nur wenn Permission bestätigt)
6) Optional:
   - Azure TTS konfigurieren (ENV)
   - Ollama target testen (wenn Ollama läuft)

## Befehle (ausführen)
```bash
cd /home/jannis/Schreibtisch/Work-OS/40_Products/WANDA/voice_mvp

sudo apt update
sudo apt install -y portaudio19-dev ffmpeg python3-tk xclip wl-clipboard

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e .

pytest -q

wanda voice devices
wanda voice --text "Hallo Test" --target stdout
wanda voice --mic --target stdout
wanda voice --mic --target insert --insert clipboard
```

## Optional: Azure TTS
```bash
export AZURE_SPEECH_KEY="..."
export AZURE_SPEECH_REGION="westeurope"
wanda voice --mic --target cli:gemini --tts azure
```

## Optional: Ollama
```bash
# Prüfen ob ollama läuft
curl -s http://127.0.0.1:11434/api/tags | head

wanda voice --mic --target cli:ollama --ollama-model llama3.1
```
