from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
import json
import os

# Minimal Chrome Trace JSON writer.
# Constraint: no overlapping B/E events on same tid (Perfetto nesting requirement).

def _now_us() -> int:
    return int(time.time() * 1_000_000)

@dataclass
class TraceEvent:
    name: str
    ph: str  # 'B','E','X','C','i',...
    ts: int
    pid: int
    tid: int
    dur: Optional[int] = None
    args: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"name": self.name, "ph": self.ph, "ts": self.ts, "pid": self.pid, "tid": self.tid}
        if self.dur is not None:
            d["dur"] = self.dur
        if self.args:
            d["args"] = self.args
        return d

class TraceRecorder:
    def __init__(self, pid: int = 1) -> None:
        self.pid = pid
        self.events: List[TraceEvent] = []
        self._tid_map: Dict[str, int] = {}
        self._tid_next = 1

    def tid(self, component: str) -> int:
        if component not in self._tid_map:
            self._tid_map[component] = self._tid_next
            self._tid_next += 1
        return self._tid_map[component]

    def span_begin(self, component: str, name: str, **args: Any) -> None:
        self.events.append(TraceEvent(name=name, ph="B", ts=_now_us(), pid=self.pid, tid=self.tid(component), args=args))

    def span_end(self, component: str, name: str, **args: Any) -> None:
        self.events.append(TraceEvent(name=name, ph="E", ts=_now_us(), pid=self.pid, tid=self.tid(component), args=args))

    def counter(self, component: str, name: str, value: float, **args: Any) -> None:
        self.events.append(TraceEvent(name=name, ph="C", ts=_now_us(), pid=self.pid, tid=self.tid(component), args={"value": value, **args}))

    def export_json(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump([e.to_json() for e in self.events], f)
