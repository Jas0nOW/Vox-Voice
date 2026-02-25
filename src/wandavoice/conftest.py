import sys
from pathlib import Path


# Ensure repository root is importable when running tests without installation.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
