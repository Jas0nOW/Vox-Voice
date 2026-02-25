import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import os

device = "cuda:0" if torch.cuda.is_available() else "cpu"

def generate_sample():
    print(f"Loading Parler-TTS on {device}...")
    model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1").to(device)
    tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")

    prompt = "Eine junge deutsche Frau mit einer klaren, sanften und professionellen Stimme. Sie spricht ruhig und deutlich."
    description = "A female speaker with a clear, soft and professional voice. She speaks calmly and clearly."
    
    text = "Hallo Jannis, ich bin WANDA. Das ist meine neue, hochauflösende Stimme. Wie gefällt sie dir?"

    input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
    prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

    print("Generating High-Quality Audio...")
    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
    audio_arr = generation.cpu().numpy().squeeze()

    out_path = "research/voice_samples/parler_premium_sample.wav"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sf.write(out_path, audio_arr, model.config.sampling_rate)
    print(f"✅ Premium Sample saved to {out_path}")

if __name__ == "__main__":
    generate_sample()
