import argparse
import asyncio

from voice_engine.config import load_config
from voice_engine.engine import VoiceEngine
from voice_engine.gateway import run_gateway

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["sim"], default="sim", help="Only 'sim' ships in this skeleton.")
    p.add_argument("--config", default="config/default.json")
    p.add_argument("--ws-host", default="127.0.0.1")
    p.add_argument("--ws-port", type=int, default=7777)
    p.add_argument("--runs-dir", default="runs")
    p.add_argument("--cas-dir", default="cas/sha256")
    p.add_argument("--autostart", action="store_true", help="Auto-start one sim session when a UI connects.")
    args = p.parse_args()
    asyncio.run(_amain(args))

async def _amain(args):
    cfg = load_config(args.config)
    engine = VoiceEngine(mode=args.mode, runs_dir=args.runs_dir, cas_dir=args.cas_dir, config=cfg)
    await run_gateway(engine=engine, host=args.ws_host, port=args.ws_port, autostart=args.autostart)

if __name__ == "__main__":
    main()
