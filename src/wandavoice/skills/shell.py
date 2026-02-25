import subprocess
import shlex

def execute_shell(command: str):
    """Executes a bash command and returns the output."""
    try:
        # Use a timeout to prevent hanging the whole system
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return f"Success:\n{result.stdout}"
        else:
            return f"Error (Exit Code {result.returncode}):\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"System Error: {str(e)}"
