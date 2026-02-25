from __future__ import annotations

import os, json, hashlib, datetime
from typing import Any, Dict, Optional

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def cas_put(cas_dir: str, content: bytes) -> str:
    h = sha256_bytes(content)
    path = os.path.join(cas_dir, h)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(content)
    return h

def write_run_manifest(runs_dir: str, session_id: str, manifest: Dict[str, Any]) -> str:
    date = datetime.date.today().isoformat()
    run_dir = os.path.join(runs_dir, date, session_id)
    os.makedirs(run_dir, exist_ok=True)
    path = os.path.join(run_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path
