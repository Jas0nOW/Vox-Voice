import json
import os
import time

class AuditLogger:
    def __init__(self, config):
        self.config = config
        self.log_path = config.AUDIT_FILE
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log(self, action: str, details: dict):
        entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        print(f"\033[90m[AUDIT] {action}\033[0m")
