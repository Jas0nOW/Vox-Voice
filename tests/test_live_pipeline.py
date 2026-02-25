import asyncio
import time
import os
import sys

# Add src to python path for testing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend/voice-engine/src')))

from voice_engine.audio.vad import SileroVAD
from voice_engine.stt.faster_whisper import FasterWhisperAdapter
from voice_engine.tts.f5_tts import F5TTSAdapter

async def mock_llm_stream(text: str):
    """Mocks an LLM stream with fake tokens."""
    await asyncio.sleep(0.5) # Fake network delay
    response = "Das ist ein simulierter Testlauf. Die Pipeline funktioniert."
    for word in response.split():
        yield word + " "
        await asyncio.sleep(0.05)

async def test_end_to_end_pipeline():
    print("=== WANDA Voice Pipeline Test ===")
    
    audio_path = os.path.join(os.path.dirname(__file__), "data/arecord_test.wav")
    if not os.path.exists(audio_path):
        print(f"WARNUNG: Test-Audio {audio_path} nicht gefunden. Test abgebrochen.")
        return

    print("[1/4] Lade KI-Modelle in den VRAM (RTX 3070)...")
    start_load = time.time()
    
    vad = SileroVAD(threshold=0.5)
    stt = FasterWhisperAdapter(model_size="large-v3-turbo", device="cuda")
    tts = F5TTSAdapter()
    
    print(f"      Modelle geladen in {time.time() - start_load:.2f}s")

    print("\\n[2/4] Simuliere Audio-Eingabe (VAD + STT)...")
    start_stt = time.time()
    
    stt_result = await stt.transcribe_file(audio_path)
    stt_latency = time.time() - start_stt
    
    print(f"      Transkription: '{stt_result.text}'")
    print(f"      STT Latenz: {stt_latency:.2f}s (Confidence: {stt_result.confidence:.2f})")

    print("\\n[3/4] LLM Inferenz (Mock)...")
    start_llm = time.time()
    first_token_time = None
    
    async def llm_generator():
        nonlocal first_token_time
        async for chunk in mock_llm_stream(stt_result.text):
            if first_token_time is None:
                first_token_time = time.time() - start_llm
                print(f"      First Token Latency: {first_token_time:.2f}s")
            yield chunk

    print("\\n[4/4] TTS Synthese (F5-TTS)...")
    start_tts = time.time()
    
    tts_chunks = []
    async for audio_bytes in tts.synthesize_stream(llm_generator()):
        tts_chunks.append(audio_bytes)
        if len(tts_chunks) == 1:
            first_audio_latency = time.time() - start_tts
            print(f"      First Audio Latency (ab TTS start): {first_audio_latency:.2f}s")
            
    total_audio_len = sum(len(c) for c in tts_chunks)
    print(f"      TTS beendet. Generierte Bytes: {total_audio_len}")
    
    print("\\n=== PIPELINE ERFOLGREICH BEENDET ===")
    print(f"End-to-End Latenz (STT -> Audio 1): {(time.time() - start_stt):.2f}s (Inklusive Mock-Netzwerk)")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_pipeline())
