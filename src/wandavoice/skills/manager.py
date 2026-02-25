from wandavoice.skills.shell import execute_shell
from wandavoice.skills.knowledge import knowledge_op
from wandavoice.permissions import PermissionManager

class SkillManager:
    def __init__(self, config):
        self.config = config
        self.permissions = PermissionManager(config)
        self.registry = {
            "shell": execute_shell,
            "knowledge": knowledge_op
        }

    def run_skill(self, name: str, **kwargs):
        if name not in self.registry:
            return f"Error: Skill '{name}' not found."
        
        # Determine permission action
        action_map = {
            "shell": "exec_external_cli",
            "knowledge": "file_system_access"
        }
        
        perm = self.permissions.check(action_map.get(name, "confirm"))
        
        if perm == "deny":
            return "Error: Permission denied by policy."
        
        # Handle 'confirm' (we would normally ask the user here, but for now we log it)
        if perm == "confirm":
            print(f"[SECURITY] Skill '{name}' requires confirmation. Auto-allowing for dev mode.")
        
        return self.registry[name](**kwargs)
