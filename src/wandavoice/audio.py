import sys
import threading
import queue
import time
import torch
import numpy as np
import subprocess
import fcntl
import os
from typing import Optional

class AudioRecorder:
    def __init__(self, config, level_callback=None):
        self.config = config
        self.target_samplerate = 16000
        self.vad_chunk_size = 512  # Silero VAD requires 512 samples at 16kHz
        self.vad_threshold = float(config.get("voice.audio.vad_threshold", 0.3))
        self.level_callback = level_callback
        self.muted = False # State for UI mute

        print(f"Audio Backend: PipeWire (pw-record) -> Native 16000Hz")

        print("Loading Silero VAD v5...", end="", flush=True)
        self.vad_model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad", model="silero_vad", trust_repo=True
        )
        print(" Done.")

    def _start_pw_record(self) -> subprocess.Popen:
        """Starts a pw-record subprocess to stream raw float32 audio at 16000Hz."""
        cmd = [
            "pw-record", 
            "--raw", 
            "--format", "f32", 
            "--channels", "1", 
            "--rate", str(self.target_samplerate), 
            "-" # stdout
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        
        # Make stdout non-blocking
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        return process

    def _read_nonblocking(self, process: subprocess.Popen, block_size_bytes: int) -> bytes:
        data = b""
        try:
            raw = process.stdout.read(block_size_bytes)
            if raw:
                if self.muted:
                    data = b"\x00" * len(raw)
                else:
                    data = raw
        except IOError:
            pass # EAGAIN
        return data

    def _start_streaming_stt(self, get_audio_fn, stt_engine, transcript_callback):
        self._stop_streaming = False
        def stream_worker():
            last_len = 0
            while not self._stop_streaming:
                time.sleep(0.5)
                audio_16k = get_audio_fn()
                if audio_16k is None or len(audio_16k) == 0:
                    continue
                
                current_len = len(audio_16k)
                if current_len > last_len + (self.target_samplerate * 0.5):
                    text = stt_engine.transcribe(audio_16k)
                    if text and transcript_callback:
                        transcript_callback(text)
                    last_len = current_len

        t = threading.Thread(target=stream_worker, daemon=True)
        t.start()
        return t

    def record_phrase(self, stt_engine=None, transcript_callback=None, cancel_token=None, vad_profile="chat") -> Optional[np.ndarray]:
        if vad_profile == "command":
            start_threshold = self.vad_threshold
            stop_threshold = min(self.vad_threshold * 0.4, 0.20)
            silence_frames_needed = 15 # ~480ms silence to stop
        else: # chat
            start_threshold = self.vad_threshold
            stop_threshold = min(self.vad_threshold * 0.4, 0.20)
            silence_frames_needed = 30 # ~960ms silence to stop

        max_samples = int(30 * self.target_samplerate)

        pre_roll_duration_s = 2.0
        pre_roll_max_samples = int(pre_roll_duration_s * self.target_samplerate)
        pre_roll_buffer = np.array([], dtype=np.float32)

        triggered = False
        speech_buffer = []
        vad_buffer = np.array([], dtype=np.float32)
        consecutive_silence = 0
        total_samples = 0

        sys.stdout.write(f"\n\033[94m ● Listening (VAD profile '{vad_profile}', threshold {start_threshold:.2f})...\033[0m\n")
        sys.stdout.flush()
        
        stream_thread = None
        if stt_engine and transcript_callback:
            stream_thread = self._start_streaming_stt(
                lambda: np.concatenate(speech_buffer) if speech_buffer else None, 
                stt_engine, 
                transcript_callback
            )

        process = self._start_pw_record()
        bytes_to_read = 4096 # 1024 floats

        try:
            while total_samples < max_samples:
                if cancel_token and cancel_token.is_cancelled():
                    sys.stdout.write("\033[90m [Cancelled]\033[0m\n")
                    break

                raw_data = self._read_nonblocking(process, bytes_to_read)
                if not raw_data:
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)
                    continue

                valid_bytes = (len(raw_data) // 4) * 4
                if valid_bytes == 0:
                    continue
                    
                chunk = np.frombuffer(raw_data[:valid_bytes], dtype=np.float32).copy()
                
                if not triggered:
                    pre_roll_buffer = np.concatenate([pre_roll_buffer, chunk])
                    if len(pre_roll_buffer) > pre_roll_max_samples:
                        pre_roll_buffer = pre_roll_buffer[-pre_roll_max_samples:]
                else:
                    total_samples += len(chunk)

                vad_buffer = np.concatenate([vad_buffer, chunk])
                
                if self.level_callback:
                    rms = np.sqrt(np.mean(chunk**2))
                    self.level_callback(rms)

                while len(vad_buffer) >= self.vad_chunk_size:
                    vad_chunk = vad_buffer[:self.vad_chunk_size]
                    vad_buffer = vad_buffer[self.vad_chunk_size:]
                    
                    chunk_tensor = torch.from_numpy(vad_chunk)
                    prob = self.vad_model(chunk_tensor, self.target_samplerate).item()

                    if not triggered:
                        if prob >= start_threshold:
                            triggered = True
                            sys.stdout.write("\033[92m ● Recording...\033[0m ")
                            sys.stdout.flush()
                            if len(pre_roll_buffer) > 0:
                                speech_buffer.append(pre_roll_buffer)
                                total_samples += len(pre_roll_buffer)
                            speech_buffer.append(vad_chunk)
                            total_samples += len(vad_chunk)
                    else:
                        speech_buffer.append(vad_chunk)
                        if prob <= stop_threshold:
                            consecutive_silence += 1
                        else:
                            consecutive_silence = 0

                if triggered and consecutive_silence >= silence_frames_needed:
                    sys.stdout.write(" Done.\n")
                    break

            if total_samples >= max_samples and triggered:
                sys.stdout.write(" [30s cap]\n")

        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stdout.write("\n")
            print(f"Capture Error: {e}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()

        if stream_thread:
            self._stop_streaming = True
            stream_thread.join(timeout=1.0)

        if self.level_callback:
            self.level_callback(0.0)

        if cancel_token and cancel_token.is_cancelled():
            return None

        if not speech_buffer:
            return None
            
        return np.concatenate(speech_buffer)


    def record_toggle(self, stop_queue: queue.Queue, stt_engine=None, transcript_callback=None) -> Optional[np.ndarray]:
        chunks = []

        sys.stdout.write("\033[91m ● Recording — press [Right Ctrl] again to stop...\033[0m\n")
        sys.stdout.flush()
        
        stream_thread = None
        if stt_engine and transcript_callback:
            stream_thread = self._start_streaming_stt(
                lambda: np.concatenate(chunks) if chunks else None, 
                stt_engine, 
                transcript_callback
            )

        process = self._start_pw_record()
        bytes_to_read = 4096

        try:
            while True:
                try:
                    stop_queue.get_nowait()
                    break
                except queue.Empty:
                    pass

                raw_data = self._read_nonblocking(process, bytes_to_read)
                if not raw_data:
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)
                    continue

                valid_bytes = (len(raw_data) // 4) * 4
                if valid_bytes > 0:
                    chunk = np.frombuffer(raw_data[:valid_bytes], dtype=np.float32).copy()
                    chunks.append(chunk)
                    if self.level_callback:
                        rms = np.sqrt(np.mean(chunk**2))
                        self.level_callback(rms)

        except Exception as e:
            print(f"\nToggle Capture Error: {e}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()

        sys.stdout.write("\033[90m ⏹ Stopped.\033[0m\n")

        if stream_thread:
            self._stop_streaming = True
            stream_thread.join(timeout=1.0)

        if self.level_callback:
            self.level_callback(0.0)

        if not chunks:
            return None
            
        return np.concatenate(chunks)

    def record_ptt(self, ptt_event: threading.Event) -> Optional[np.ndarray]:
        chunks = []

        sys.stdout.write("\033[92m ● Recording (PTT)...\033[0m")
        sys.stdout.flush()

        process = self._start_pw_record()
        bytes_to_read = 4096

        try:
            while ptt_event.is_set():
                raw_data = self._read_nonblocking(process, bytes_to_read)
                if not raw_data:
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)
                    continue

                valid_bytes = (len(raw_data) // 4) * 4
                if valid_bytes > 0:
                    chunk = np.frombuffer(raw_data[:valid_bytes], dtype=np.float32).copy()
                    chunks.append(chunk)
                    if self.level_callback:
                        rms = np.sqrt(np.mean(chunk**2))
                        self.level_callback(rms)
        except Exception as e:
            print(f"\nPTT Capture Error: {e}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                process.kill()

        sys.stdout.write(" Released.\n")
        
        if self.level_callback:
            self.level_callback(0.0)

        if not chunks:
            return None
            
        return np.concatenate(chunks)

    def record_fixed(self, duration_s: int = 5) -> np.ndarray:
        print(f"\033[93m!!! STARTING {duration_s}s capture !!!\033[0m")
        
        process = self._start_pw_record()
        total_samples = int(duration_s * self.target_samplerate)
        bytes_to_read = total_samples * 4
        
        raw_data = b""
        import fcntl
        # restore blocking IO just for this
        fd = process.stdout.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl & ~os.O_NONBLOCK)
        
        while len(raw_data) < bytes_to_read:
            chunk = process.stdout.read(min(4096, bytes_to_read - len(raw_data)))
            if not chunk:
                break
            raw_data += chunk
            
        process.terminate()
        
        result = np.frombuffer(raw_data, dtype=np.float32)
        return result
