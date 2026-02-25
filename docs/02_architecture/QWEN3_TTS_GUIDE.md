# Qwen3-TTS Implementierungs-Guide (SOTA 2026)

## Strategie
Qwen3 nutzt "Intelligent Control". Die Stimme wird nicht geklont, sondern per Text beschrieben.

## Anforderungen
- Python 3.12+
- transformers >= 4.57.3
- qwen-tts (Official package)
- CUDA 12.1+

## Voice Design Prompt (WANDA Aura)
"Eine deutsche Frauenstimme, ausdrucksstark und lebendig, mit einer warmen und freundlichen Tonlage. Klare Artikulation, Jarvis-Vibe."

## Inferenz-Code
```python
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice")
wavs, sr = model.generate_custom_voice(text=text, language="German", instruct=prompt)
```
