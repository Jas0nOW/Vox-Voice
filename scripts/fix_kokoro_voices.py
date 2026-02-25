import json
import os

# Manual fix for Kokoro voices.json to include German SOTA mappings
# based on Feb 2026 community standards
VOICES_DATA = {
    "de_01": {"name": "Female - Clear", "lang": "de"},
    "de_03": {"name": "Female - Soft", "lang": "de"},
    "de_05": {"name": "Female - Professional", "lang": "de"},
    "af_heart": {"name": "English - Iconic", "lang": "en-us"}
}

def fix_voices():
    path = os.path.expanduser("~/.wanda/models/kokoro/voices.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(VOICES_DATA, f, indent=2)
    print(f"Fixed voices.json at {path}")

if __name__ == "__main__":
    fix_voices()
