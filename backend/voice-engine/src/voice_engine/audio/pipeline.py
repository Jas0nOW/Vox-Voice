from __future__ import annotations

import asyncio
import queue
import sounddevice as sd
import numpy as np
from typing import Callable, Optional

class AudioPipeline:
    def __init__(
        self, 
        sample_rate: int = 16000, 
        channels: int = 1, 
        chunk_size: int = 512,
        on_audio_level: Optional[Callable[[float], None]] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.on_audio_level = on_audio_level
        
        self._queue: queue.Queue[bytes] = queue.Queue()
        self._stream: Optional[sd.InputStream] = None
        self._running = False

    def _callback(self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags):
        if status:
            print(f"Audio Status: {status}")
            
        # Calculate RMS for audio level event
        if self.on_audio_level:
            rms = np.sqrt(np.mean(indata**2))
            self.on_audio_level(float(rms))
            
        # Put raw bytes into queue
        self._queue.put(indata.tobytes())

    def start(self):
        self._running = True
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._callback,
            blocksize=self.chunk_size,
            dtype='int16'
        )
        self._stream.start()

    def stop(self):
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()

    async def stream(self):
        """Generator that yields audio chunks as they arrive."""
        while self._running or not self._queue.empty():
            try:
                # Use a small timeout to allow checking _running
                chunk = await asyncio.to_thread(self._queue.get, timeout=0.1)
                yield chunk
            except queue.Empty:
                await asyncio.sleep(0.01)
                continue
