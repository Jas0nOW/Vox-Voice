import os
import sys
# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from wandavoice.config import Config
from wandavoice.llm import GeminiLLM

def test_llm():
    cfg = Config()
    llm = GeminiLLM(cfg)
    history = []
    prompt = "Speichere das Rezept für einen Erdbeerkuchen als Notiz für NotebookLM."
    
    print(f"Testing Prompt: {prompt}")
    response = llm.generate(prompt, history)
    print("--- RAW RESPONSE ---")
    print(response)
    print("--------------------")

if __name__ == "__main__":
    test_llm()
