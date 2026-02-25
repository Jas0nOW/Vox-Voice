from dataclasses import dataclass, field
from typing import Optional, Dict

@dataclass
class RuntimeOptions:
    target: str = "stdout"
    insert_mode: str = "off"
    tts_mode: str = "none"
    safe_mode: bool = True

def apply_safe_overrides(options: RuntimeOptions) -> RuntimeOptions:
    """Zwingt Optionen in einen sicheren Zustand, wenn safe_mode aktiv ist."""
    if options.safe_mode:
        options.target = "stdout"
        options.insert_mode = "off"
        options.tts_mode = "none"
    return options

class RouterResponse:
    def __init__(self, target_used: str, inserted: bool = False, fallback_to_stdout: bool = False):
        self.target_used = target_used
        self.inserted = inserted
        self.fallback_to_stdout = fallback_to_stdout

class Router:
    def __init__(self, config=None, permissions=None, audit=None, inserter=None):
        self.config = config
        self.permissions = permissions
        self.audit = audit
        self.inserter = inserter

    def route_text(self, text: str, options: RuntimeOptions, prompt: Optional[str] = None) -> RouterResponse:
        # Check permissions for target
        if options.target == "insert":
            perm = self.permissions.config.get_permission("window_inject")
            if perm == "allow":
                if self.inserter:
                    self.inserter.insert_text(text, options.insert_mode)
                return RouterResponse(target_used="insert", inserted=True)
            else:
                # Fallback to stdout
                return RouterResponse(target_used="stdout", fallback_to_stdout=True)
        
        return RouterResponse(target_used="stdout")
