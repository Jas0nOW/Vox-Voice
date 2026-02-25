
# Contributing

## Dev Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e .
pytest -q
```

## Guidelines
- Keep changes minimal-risk and documented.
- Prefer small adapters over hard coupling.
- Never add default behaviors that inject into windows or call external CLIs without explicit opt-in.
