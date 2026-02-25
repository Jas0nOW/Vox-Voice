import sounddevice as sd
import numpy as np
import time

def scan_devices():
    devices = sd.query_devices()
    input_devices = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    
    print(f"Starting Scan of {len(input_devices)} devices. Please speak continuously!")
    
    for i in input_devices:
        d = devices[i]
        print(f"\n[DEVICE {i}] {d['name']}")
        try:
            samplerate = int(d['default_samplerate'])
            if samplerate <= 0: samplerate = 44100
            recording = sd.rec(int(2 * samplerate), samplerate=samplerate, channels=1, device=i, dtype='float32')
            sd.wait()
            amp = np.max(np.abs(recording))
            print(f"  -> Peak Level: {amp:.4f}")
            if amp > 0.05:
                print(f"  SUCCESS: Signal detected on Device {i}!")
        except Exception as e:
            print(f"  -> Skip: {e}")

if __name__ == "__main__":
    scan_devices()
