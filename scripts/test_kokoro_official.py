from kokoro import KPipeline
import soundfile as sf
import os

def generate_kokoro():
    print("Initializing Kokoro Pipeline (German)...")
    pipeline = KPipeline(lang_code='d') 
    text = "Hallo Jannis, ich bin WANDA. Das ist meine Stimme im Kokoro Modus. Sie ist schnell und klar."
    generator = pipeline(text, voice='df_sarah', speed=1, split_pattern=r'\n+')
    for i, (gs, ps, audio) in enumerate(generator):
        out_path = "research/voice_samples/kokoro_de_sample.wav"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        sf.write(out_path, audio, 24000)
        print(f"✅ Kokoro Sample saved to {out_path}")

if __name__ == "__main__":
    generate_kokoro()
