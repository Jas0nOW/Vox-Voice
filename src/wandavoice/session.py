import json
import os
import time
from typing import List, Dict

class SessionManager:
    def __init__(self, config):
        self.config = config
        self.config.ensure_dirs()
        self.filepath = self.config.SESSION_FILE
        
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w') as f:
                pass

    def add_turn(self, role: str, text: str):
        entry = {
            "ts": time.time(),
            "role": role,
            "text": text
        }
        with open(self.filepath, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    def get_history(self) -> List[Dict]:
        turns = []
        if not os.path.exists(self.filepath):
            return []
            
        with open(self.filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        turns.append(json.loads(line))
                    except:
                        continue
        
        # Return last N turns
        return turns[-self.config.HISTORY_TURNS:]
