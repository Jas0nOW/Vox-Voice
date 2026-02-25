import os
import sys
import wave
import io
import sounddevice as sd
import numpy as np
import librosa
import torch
from abc import ABC, abstractmethod
from typing import Optional

try:
    from orpheus_cpp import OrpheusCpp
except ImportError:
    OrpheusCpp = None


class BaseTTS(ABC):
    @abstractmethod
    def speak(self, text: str):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def wait(self):
        pass


class OrpheusSOTA(BaseTTS):
    def __init__(self, config):
        self.config = config
        self.enabled = False
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        if OrpheusCpp:
            try:
                print("Loading Orpheus 3B SOTA Model...")
                self.tts_engine = OrpheusCpp(lang="de", n_gpu_layers=30, verbose=False)
                self.enabled = True
            except Exception as e:
                print(f"Orpheus Load Error: {e}")

    def speak(self, text: str):
        if not self.enabled:
            return
        try:
            sample_rate, audio_arr = self.tts_engine.tts(text)

            if audio_arr.dtype == np.int16:
                audio_np = audio_arr.astype(np.float32) / 32768.0
            else:
                audio_np = audio_arr

            sd.play(audio_np, samplerate=sample_rate, blocking=False)
        except Exception as e:
            print(f"Orpheus TTS Error: {e}")

    def stop(self):
        sd.stop()

    def wait(self):
        sd.wait()


class EdgeSeraphina(BaseTTS):
    def __init__(self, config):
        self.config = config
        self.enabled = True
        self.voice = "de-DE-SeraphinaMultilingualNeural"
        print("Loading Edge TTS (Seraphina) Streaming Queue...")
        
        import queue
        import threading
        
        self.text_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.running = True
        self._playback_process = None
        
        self.gen_thread = threading.Thread(target=self._generator_worker, daemon=True)
        self.play_thread = threading.Thread(target=self._player_worker, daemon=True)
        
        self.gen_thread.start()
        self.play_thread.start()

    def speak(self, text: str):
        if not self.enabled:
            return
        if not text.strip():
            return
        self.text_queue.put(text)

    def _generator_worker(self):
        import subprocess
        import tempfile
        import time
        import queue
        
        while self.running:
            try:
                text = self.text_queue.get(timeout=0.1)
            except queue.Empty:
                continue
                
            if text is None:
                self.text_queue.task_done()
                break
                
            temp_path = None
            wav_path = None
            try:
                gen_start = time.perf_counter()
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    temp_path = f.name
                
                wav_path = temp_path.replace(".mp3", ".wav")
                
                subprocess.run(
                    [
                        sys.executable, "-m", "edge_tts",
                        "--voice", self.voice,
                        "--text", text,
                        "--rate", "+15%",
                        "--write-media", temp_path,
                    ],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                
                subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_path, "-ac", "1", "-ar", "24000", wav_path],
                    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                )
                
                gen_elapsed = (time.perf_counter() - gen_start) * 1000
                print(f"\033[90m[TTS Gen] '{text[:20]}...' in {gen_elapsed:.0f}ms\033[0m")
                
                self.audio_queue.put(wav_path)
                
            except Exception as e:
                print(f"Edge TTS Gen Error: {e}")
                if wav_path:
                    try: os.remove(wav_path)
                    except: pass
            finally:
                if temp_path:
                    try: os.remove(temp_path)
                    except: pass
                
            self.text_queue.task_done()

    def _player_worker(self):
        import subprocess
        import queue
        while self.running:
            try:
                wav_path = self.audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue
                
            if wav_path is None:
                self.audio_queue.task_done()
                break
                
            try:
                self._playback_process = subprocess.Popen(
                    ["pw-play", wav_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._playback_process.wait()
                
                try:
                    os.remove(wav_path)
                except: pass
                
            except Exception as e:
                print(f"Edge TTS Play Error: {e}")
                
            self.audio_queue.task_done()

    def stop(self):
        sd.stop()
        
        import queue
        while not self.text_queue.empty():
            try: self.text_queue.get_nowait(); self.text_queue.task_done()
            except queue.Empty: break
            
        while not self.audio_queue.empty():
            try:
                wav_path = self.audio_queue.get_nowait()
                try: os.remove(wav_path)
                except: pass
                self.audio_queue.task_done()
            except queue.Empty: break
            
        if self._playback_process:
            import subprocess
            try:
                self._playback_process.terminate()
                try:
                    self._playback_process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    self._playback_process.kill()
            except:
                pass

    def wait(self):
        self.text_queue.join()
        self.audio_queue.join()


class TTSEngine:
    def __init__(self, config):
        self.config = config
        mode = config.get("voice.routing.tts", "seraphina")

        if mode == "orpheus":
            self.engine = OrpheusSOTA(config)
        else:
            self.engine = EdgeSeraphina(config)

        self.enabled = self.engine.enabled

    def speak(self, text: str):
        if self.engine:
            self.engine.speak(text)

    def stop(self):
        if self.engine:
            self.engine.stop()

    def wait(self):
        if self.engine:
            self.engine.wait()
