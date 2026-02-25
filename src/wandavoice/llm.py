import subprocess
import shutil
import json
import re
import os
from typing import List, Dict, Tuple

class GeminiLLM:
    def __init__(self, config):
        self.config = config
        self.executable = shutil.which("gemini")
        if not self.executable:
            raise EnvironmentError("Gemini CLI ('gemini') not found in PATH.")
        
        self.runtime_home = os.path.abspath(".runtime/gemini_home")
        os.makedirs(self.runtime_home, exist_ok=True)
        self._link_auth()

    def _link_auth(self):
        real_gemini_dir = os.path.expanduser("~/.gemini")
        target_gemini_dir = os.path.join(self.runtime_home, ".gemini")
        if os.path.exists(real_gemini_dir):
            if not os.path.exists(target_gemini_dir):
                os.symlink(real_gemini_dir, target_gemini_dir)

    def generate_stream(self, prompt: str, history: List[Dict]):
        # Cleaner context building
        context = ""
        for turn in history[-6:]: # last 3 turns (user+assistant)
            role = "USER" if turn['role'] == 'user' else "WANDA"
            # Strip tags for history context to avoid recursive confusion
            text = turn['text'].replace("SAY: ", "").replace("SHOW: ", "").replace("\n", " ")
            context += f"{role}: {text}\n"

        system_instruction = (
            "SYSTEM: You are WANDA, a professional AI-Architect and Voice-OS.\n"
            "MANDATORY FORMAT:\n"
            "SAY: [Short spoken answer]\n"
            "SHOW: [Markdown info]\n"
            "SKILL: [Optional: skill_name(args)]\n\n"
            "SKILLS AVAILABLE:\n"
            "- knowledge(op='sync_notebooklm', title='...', content='...') # Saves notes to Google Drive\n"
            "- shell(command='...') # Runs shell commands\n"
        )
        
        full_prompt = f"{system_instruction}\nCONTEXT:\n{context}\nUSER: {prompt}\nWANDA:"

        cmd = [self.executable, "-p", full_prompt, "--output-format", "stream-json"]
        
        env = os.environ.copy()
        env["HOME"] = self.runtime_home
        env["GEMINI_SKIP_UPDATE_CHECK"] = "1"
        # Force OAuth/Personal if configured in real home
        env["GEMINI_AUTH_TYPE"] = "oauth-personal"

        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, env=env, bufsize=1
            )

            for line in process.stdout:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    chunk = data.get('content', data.get('response', ''))
                    if chunk: yield chunk
                except json.JSONDecodeError:
                    yield line
        except Exception as e:
            yield f"SAY: System error.\nSHOW: {e}"

    def generate(self, prompt: str, history: List[Dict]) -> str:
        return "".join(list(self.generate_stream(prompt, history)))

    def parse_response(self, raw: str) -> Tuple[str, str]:
        say = ""
        show = ""
        clean = raw.strip()
        
        # Robust parsing
        say_match = re.search(r"SAY:\s*(.*?)(?=\s*SHOW:|\s*SKILL:|$)", clean, re.DOTALL | re.IGNORECASE)
        show_match = re.search(r"SHOW:\s*(.*?)(?=\s*SKILL:|$)", clean, re.DOTALL | re.IGNORECASE)
        
        if say_match: say = say_match.group(1).strip()
        if show_match: show = show_match.group(1).strip()
        
        if not say:
            # Fallback if tags missing
            say = clean.split("\n")[0]
            show = clean
            
        return say, show
