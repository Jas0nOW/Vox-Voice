import time
import threading
from typing import Dict, List

class CancelToken:
    def __init__(self):
        self._cancelled = threading.Event()
        
    def cancel(self):
        self._cancelled.set()
        
    def is_cancelled(self) -> bool:
        return self._cancelled.is_set()

    def reset(self):
        self._cancelled.clear()

class LatencyTracker:
    def __init__(self):
        self.reset()

    def reset(self):
        self.start_times: Dict[str, float] = {}
        self.measurements: List[Dict] = []
        self._global_start = time.perf_counter()

    def start(self, label: str):
        self.start_times[label] = time.perf_counter()

    def stop(self, label: str):
        if label in self.start_times:
            end_time = time.perf_counter()
            elapsed = (end_time - self.start_times[label]) * 1000
            # Store with absolute timestamp relative to global start for timeline debugging
            abs_start = (self.start_times[label] - self._global_start) * 1000
            self.measurements.append({
                "label": label,
                "ms": elapsed,
                "abs_start": abs_start,
                "abs_end": abs_start + elapsed
            })
            return elapsed
        return 0.0

    def get_summary(self) -> Dict[str, float]:
        return {m["label"]: m["ms"] for m in self.measurements}

    def format_report(self) -> str:
        lines = ["\n\033[1;30m┌── TELEMETRY REPORT ──────────────────────────────────────────┐\033[0m"]
        total_pipeline = 0
        if self.measurements:
            total_pipeline = self.measurements[-1]["abs_end"] - self.measurements[0]["abs_start"]

        for m in self.measurements:
            bar = "█" * min(int(m["ms"] / 100), 20)
            lines.append(f"\033[1;30m│\033[0m {m['label']:<12} : {m['ms']:>7.1f} ms  \033[34m{bar:<20}\033[0m \033[90m(at {m['abs_start']:>7.1f}ms)\033[0m")
        
        lines.append(f"\033[1;30m├── TOTAL ROUNDTRIP: {total_pipeline:>7.1f} ms ─────────────────────────────┘\033[0m")
        return "\n".join(lines)

def print_status(msg: str):
    print(f"\033[94m[*] {msg}\033[0m")

def print_user(msg: str):
    print(f"\n\033[1;92mUSER > {msg}\033[0m")

def print_say(msg: str):
    print(f"\033[1;92mVOX SAY > {msg}\033[0m")

def print_show(msg: str):
    print(f"\033[96mVOX SHOW >\033[0m\n{msg}\n")

def print_debug(msg: str):
    print(f"\033[1;30m[DEBUG]\033[0m {msg}")
