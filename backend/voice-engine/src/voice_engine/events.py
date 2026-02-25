from __future__ import annotations

from typing import Any, Literal, Optional, Dict
from pydantic import BaseModel, Field
from ulid import ULID
import time

SchemaVersion = Literal["1.0"]

def now_unix_ms() -> int:
    return int(time.time() * 1000)

class EventEnvelope(BaseModel):
    schema_version: SchemaVersion = "1.0"
    event_id: str = Field(default_factory=lambda: str(ULID()))
    session_id: str
    ts_unix_ms: int = Field(default_factory=now_unix_ms)
    component: str
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class Command(BaseModel):
    # from UI → engine
    type: str
    session_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
