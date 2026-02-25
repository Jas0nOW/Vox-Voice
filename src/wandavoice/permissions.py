class PermissionManager:
    def __init__(self, config, safe_mode: bool = False, interactive: bool = True):
        self.config = config
        self.safe_mode = safe_mode
        self.interactive = interactive

    def check(self, action: str) -> str:
        if self.safe_mode:
            return "deny"
        
        # Mapping for config-based permissions
        scope_map = {
            "window_inject": "window_inject",
            "shell_execute": "exec_external_cli",
            "clipboard_write": "clipboard_write"
        }
        
        scope = scope_map.get(action, action)
        return self.config.get_permission(scope)
