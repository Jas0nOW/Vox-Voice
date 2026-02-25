# Tutorial: Frontend (MCC + Orb)

## MCC (web)
Serve static files:
```bash
python -m http.server 5173 --directory frontend/mcc
```
Open `http://127.0.0.1:5173`.

It connects to `ws://127.0.0.1:7777/ws/events` by default.

## Orb (GTK4 layer-shell)
Prereqs (Debian/Ubuntu style):
- GTK4 + python GI (python3-gi)
- gtk4-layer-shell + GI typelibs
- python websockets

Run:
```bash
cd frontend/orb
python -m venv .venv && source .venv/bin/activate
pip install websockets
python orb.py --ws ws://127.0.0.1:7777/ws/events
```
