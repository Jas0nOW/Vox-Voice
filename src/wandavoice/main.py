import click
import sys
import os
import threading
import queue
import time
import soundfile as sf
import subprocess

# os.environ["GDK_BACKEND"] = "x11" # Removed global X11 override to support GTK4 Layer Shell
# os.environ["QT_QPA_PLATFORM"] = "xcb" # If we ever use Qt
os.environ["HF_TOKEN"] = os.getenv("WANDA_HF_TOKEN", "")

from wandavoice.config import Config
from wandavoice.audio import AudioRecorder
from wandavoice.stt import STTEngine
from wandavoice.llm import GeminiLLM
from wandavoice.tts import TTSEngine
from wandavoice.session import SessionManager
from wandavoice.utils import print_status, print_user, print_say, print_show
from wandavoice.ui import VoxOrb, MissionControl
from wandavoice.insert import insert_text
from wandavoice import mcc_server

# New professional components
from wandavoice.router import Router, RuntimeOptions
from wandavoice.permissions import PermissionManager
from wandavoice.audit import AuditLogger
from wandavoice.skills.manager import SkillManager


def get_ui_python():
    """Returns a python path that has 'gi' (GObject) installed.
    Prefers system python on Pop!_OS to avoid Homebrew mismatch."""
    system_py = "/usr/bin/python3"
    try:
        # Check if system python has GI
        if subprocess.call([system_py, "-c", "import gi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            return system_py
    except Exception:
        pass
    return sys.executable # Fallback


def get_ui_env():
    """Returns a dictionary of environment variables optimized for GTK4/Wayland on NVIDIA."""
    env = os.environ.copy()
    env["GDK_BACKEND"] = "wayland"
    
    # Fallback to cairo renderer (CPU) to bypass EGL provider issues on NVIDIA/COSMIC
    # This is much more stable for floating/layered windows on Wayland+NVIDIA
    env["GSK_RENDERER"] = "cairo"
    
    # LD_PRELOAD fix for the GTK4 Layer Shell GI bindings
    env["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libgtk4-layer-shell.so"
    return env


# ─── evdev Right Ctrl listener ─────────────────────────────────────────────
def start_evdev_listener(key_queue: queue.Queue, shutdown: threading.Event) -> bool:
    try:
        import evdev
        from evdev import ecodes

        seen_phys: set = set()
        keyboards = []
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps and ecodes.KEY_RIGHTCTRL in caps[ecodes.EV_KEY]:
                    phys = dev.phys or dev.name or path
                    base = phys.rsplit("/input", 1)[0]
                    if base not in seen_phys:
                        seen_phys.add(base)
                        keyboards.append(dev)
            except Exception:
                pass

        if not keyboards:
            return False

        import selectors
        sel = selectors.DefaultSelector()
        for dev in keyboards:
            sel.register(dev, selectors.EVENT_READ)

        def _listen():
            while not shutdown.is_set():
                for key, _ in sel.select(timeout=0.1):
                    dev = key.fileobj
                    try:
                        for event in dev.read():
                            if event.type == ecodes.EV_KEY and event.code == ecodes.KEY_RIGHTCTRL and event.value == 1:
                                key_queue.put(())
                    except Exception:
                        pass

        t = threading.Thread(target=_listen, daemon=True, name="evdev-listener")
        t.start()
        return True

    except Exception as e:
        print_status(f"evdev init error: {e}")
        return False


# ─── CLI ───────────────────────────────────────────────────────────────────

@click.group()
def cli():
    """VOX Voice & Mission Control CLI"""
    pass


@cli.command()
def mcc():
    """Start the Mission Control Center (Web UI Dashboard)"""
    from wandavoice.mcc_server import start_mcc_server
    print_status("Starting real Web MCC Dashboard...")
    start_mcc_server()
    print_status("Dashboard is running on http://127.0.0.1:5173")
    print_status("Press Ctrl+C to close this terminal wrapper (Dashboard stays alive).")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Goodbye.")


def handle_mcc_command(cmd, cfg, recorder=None, tts_engine=None, orb_ui=None):
    try:
        ctype = cmd.get("type")
        payload = cmd.get("payload", {})
        
        if ctype == "set_llm_profile":
            prof = payload.get("profile")
            print_status(f"[MCC] Applied LLM Profile: {prof}")
            if prof == "fast":
                cfg.update_from_args(model="gemini-3-flash-preview")
            elif prof == "reasoning":
                cfg.update_from_args(model="gemini-3-pro-preview")
                
        elif ctype == "set_stt_profile":
            prof = payload.get("profile")
            print_status(f"[MCC] Applied STT Profile: {prof}")
            if prof == "fast":
                cfg.update_from_args(model="small")
            elif prof == "final":
                cfg.update_from_args(model="large-v3-turbo")

        elif ctype == "set_tts_voice":
            v = payload.get("voice", "")
            print_status(f"[MCC] Applied TTS Voice: {v}")
            cfg.update_from_args(tts="seraphina" if "seraphina" in v else "none")
            
        elif ctype == "set_routing_mode":
            mode = payload.get("mode")
            print_status(f"[MCC] Routing Mode -> {mode}")
            cfg.update_from_args(target="insert" if mode == "WINDOW_INSERT" else "cli:gemini")

        elif ctype == "set_console_mode":
            mode = payload.get("mode")
            print_status(f"[MCC] Console Mode -> {mode}")
            
        elif ctype == "orb_frame_stats":
            mcc_server.broadcast("orb_frame_stats", payload)
            
        elif ctype == "stop":
            print_status("[MCC] Action: STOP (Interrupting TTS)")
            if tts_engine:
                tts_engine.stop()
            if orb_ui:
                orb_ui.set_state("idle")
                
        elif ctype == "mute":
            # Toggle mute state
            is_muted = payload.get("muted", True)
            print_status(f"[MCC] Action: MUTE ({is_muted})")
            if recorder:
                recorder.muted = is_muted
            if orb_ui:
                orb_ui.set_state("muted" if is_muted else "idle")
                
        elif ctype == "sleep":
            print_status("[MCC] Action: SLEEP")
            if tts_engine: tts_engine.stop()
            if orb_ui: orb_ui.set_state("sleeping")
            
    except Exception as e:
        print_status(f"[MCC] Command Error: {e}")

@cli.command()
@click.option("--ws", default="ws://127.0.0.1:7777/ws/events", help="WebSocket URL")
def aura(ws):
    """Start only the VOX Aura (GTK4 Animation)."""
    orb_path = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/frontend/orb/orb.py")
    if os.path.exists(orb_path):
        print_status("Launching Standalone VOX Aura...")
        subprocess.run([get_ui_python(), orb_path, "--ws", ws], env=get_ui_env())
    else:
        print("\033[91mError: Aura script not found.\033[0m")

@cli.command()
@click.option("--ws", default="ws://127.0.0.1:7777/ws/events", help="WebSocket URL")
def console(ws):
    """Start only the VOX Console & Pill (tkinter)."""
    cfg = Config()
    orb_ui = VoxOrb(cfg)
    print_status("Launching Standalone VOX Console & Pill...")
    orb_ui.run_standalone(ws)

@cli.command()
@click.pass_context
@click.option("--no-aura", is_flag=True, help="Disable GTK4 Aura")
@click.option("--no-console", is_flag=True, help="Disable tkinter Console/Pill")
def start(ctx, no_aura, no_console):
    """Start the VOX Voice engine (Alias for 'voice')."""
    ctx.invoke(voice, no_aura=no_aura, no_console=no_console)

@cli.command()
@click.option("--text", help="Send text input (no mic).")
@click.option("--model", default="large-v3-turbo", help="Whisper model (large-v3, large-v3-turbo).")
@click.option("--tts", help="TTS engine (orpheus, seraphina, none).")
@click.option("--reset", is_flag=True, help="Clear session history.")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option("--no-hotkey", is_flag=True, help="Disable Right Ctrl hotkey, use VAD only.")
@click.option("--target", help="Override target (e.g., 'insert', 'cli:gemini').")
@click.option("--no-aura", is_flag=True, help="Disable GTK4 Aura")
@click.option("--no-console", is_flag=True, help="Disable tkinter Console/Pill")
def voice(text, model, tts, reset, debug, no_hotkey, target, no_aura, no_console):
    """Start VOX Voice (Assistant mode or Insert mode)"""
    from wandavoice.process_manager import acquire_lock, release_lock
    if not acquire_lock():
        print("\033[91m[!] Another VOX engine is already running.\033[0m")
        print("Run 'vox kill' to terminate it first.")
        sys.exit(1)
        
    cfg = Config()


    # Apply overrides
    kwargs = {"model": model, "tts": tts}
    if target: kwargs["target"] = target
    cfg.update_from_args(**kwargs)

    if debug:
        print_status("[DEBUG] Debug logging enabled.")
        import logging
        logging.basicConfig(level=logging.DEBUG)

    session = SessionManager(cfg)
    if reset:
        if os.path.exists(cfg.SESSION_FILE):
            os.remove(cfg.SESSION_FILE)
            print_status("Session history reset.")
            session = SessionManager(cfg)

    orb_ui = VoxOrb(cfg)
    # Note: MCC server start is deferred until engines are ready

    orb_ui.set_state("loading")

    try:
        recorder = AudioRecorder(cfg, level_callback=orb_ui.set_audio_level)
        stt = STTEngine(cfg)
        llm = GeminiLLM(cfg)
        tts_engine = TTSEngine(cfg)
        
        # Initialize Managers
        audit_log = AuditLogger(cfg)
        perm_mgr = PermissionManager(cfg)
        skill_mgr = SkillManager(cfg)
        router = Router(cfg, permissions=perm_mgr, audit=audit_log)
        
        managers = {
            "audit": audit_log,
            "permissions": perm_mgr,
            "skills": skill_mgr,
            "router": router
        }
        
        print_status(f"VOX Online | STT: {model} | TTS: {cfg.TTS_MODE} | Target: {cfg.TARGET}")
    except Exception as e:
        print(f"\033[91mInit Error:\033[0m {e}")
        if debug: import traceback; traceback.print_exc()
        release_lock()
        sys.exit(1)

    # Now that engines are ready, start UI and MCC Backend
    if orb_ui.enabled:
        from wandavoice.mcc_server import start_mcc_server
        print_status("Starting Web MCC Backend...")
        start_mcc_server(cmd_callback=lambda c: handle_mcc_command(c, cfg, recorder=recorder, tts_engine=tts_engine, orb_ui=orb_ui))
        
        # Priority: GTK4 Layer Shell Orb
        use_gtk = cfg.get("voice.ui.use_gtk4", True) and not no_aura
        if use_gtk:
            orb_path = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/frontend/orb/orb.py")
            if os.path.exists(orb_path):
                print_status("Launching GTK4 Layer Shell Aura...")
                orb_ui._gtk_process = subprocess.Popen(
                    [get_ui_python(), orb_path, "--ws", "ws://127.0.0.1:7777/ws/events", "--cmd", "ws://127.0.0.1:7777/ws/command"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=get_ui_env()
                )
            else:
                use_gtk = False
        
        # Start the tkinter thread for Console & Pill if not disabled
        if not no_console:
            print_status("Starting VOX Console & VOX Pill (Desktop)...")
            orb_thread = threading.Thread(
                target=orb_ui.run, 
                kwargs={"show_pill": True}, 
                daemon=True, 
                name="orb-ui"
            )
            orb_thread.start()
            orb_ui._ready.wait(timeout=3)
        else:
            # We still need to set the ready event if UI is disabled but thread is skipped
            orb_ui._ready.set()

    orb_ui.set_state("idle")

    if text:
        process_turn(text, session, llm, tts_engine, orb_ui, cfg, managers)
        release_lock()
        return

    hotkey_enabled = not no_hotkey and cfg.get("voice.ui.ptt_enabled", True)
    key_queue: queue.Queue = queue.Queue()
    shutdown = threading.Event()
    toggle_mode = False

    if hotkey_enabled:
        ok = start_evdev_listener(key_queue, shutdown)
        if ok:
            toggle_mode = True
            print_status("🎤 Toggle mode: [Right Ctrl] = Start/Stop recording | Ctrl+C = Quit")
        else:
            print_status("⚠  No keyboard found via evdev. Falling back to VAD mode.")

    if not toggle_mode:
        print_status("🎤 VAD mode: speak when VOX is listening | Ctrl+C = Quit")

    STOP_WORDS = {"stop", "stopp", "halt", "abbrechen"}

    try:
        while True:
            try:
                orb_ui.set_state("idle")
                tts_engine.stop()

                if toggle_mode:
                    print_status("Press [Right Ctrl] to start recording...")
                    key_queue.get()
                    time.sleep(0.1)  # Debounce delay
                    while not key_queue.empty():
                        try:
                            key_queue.get_nowait()
                        except queue.Empty:
                            pass

                    orb_ui.set_state("listening")
                    audio_data = recorder.record_toggle(
                        key_queue, 
                        stt_engine=stt, 
                        transcript_callback=orb_ui.set_transcript
                    )
                else:
                    orb_ui.set_state("listening")
                    from wandavoice.utils import CancelToken
                    cancel_token = CancelToken()
                    
                    # Optional: in the future we can determine vad_profile dynamically
                    vad_profile = cfg.get("voice.audio.vad_profile", "chat")
                    
                    audio_data = recorder.record_phrase(
                        stt_engine=stt, 
                        transcript_callback=orb_ui.set_transcript,
                        cancel_token=cancel_token,
                        vad_profile=vad_profile
                    )

                if audio_data is None:
                    continue

                orb_ui.set_state("thinking")
                if debug: print_status("[DEBUG] Finalizing transcription...")
                
                # 1. STT Phase with Telemetry
                from wandavoice.utils import LatencyTracker
                lt = LatencyTracker()
                lt.start("STT_Finalize")
                user_text = stt.transcribe(audio_data)
                lt.stop("STT_Finalize")

                if not user_text or not user_text.strip():
                    print_status("(nothing understood — try speaking more clearly)")
                    orb_ui.set_state("idle")
                    continue

                print_user(user_text)
                orb_ui.set_transcript(user_text)

                user_text_clean = user_text.lower().strip(".!? ")
                if user_text_clean in STOP_WORDS or any(user_text_clean.endswith(w) for w in ["neu aufnehmen", "von vorne", "nochmal", "abbrechen"]):
                    print_status("🛑 Discarding (Restart/Stop command).")
                    orb_ui.set_state("idle")
                    continue

                process_turn(user_text, session, llm, tts_engine, orb_ui, cfg, managers, lt=lt)

            except KeyboardInterrupt:
                shutdown.set()
                orb_ui.stop()
                print("\nGoodbye.")
                break
            except Exception as e:
                print(f"Loop Error: {e}")
                if debug: import traceback; traceback.print_exc()
    finally:
        release_lock()


@cli.command()
@click.option("--model", default="large-v3-turbo", help="Whisper model.")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
def dictate(model, debug):
    """Pure STT Dictation: Transcribe and insert directly into active window."""
    cfg = Config()
    cfg.update_from_args(model=model, target="insert")
    
    if debug:
        print_status("[DEBUG] Debug logging enabled.")

    orb_ui = VoxOrb(cfg)
    if orb_ui.enabled:
        from wandavoice.mcc_server import start_mcc_server
        print_status("Starting Web MCC Backend...")
        start_mcc_server(cmd_callback=lambda c: handle_mcc_command(c, cfg, recorder=recorder, tts_engine=tts_engine, orb_ui=orb_ui))
        
        # Priority: GTK4 Layer Shell Orb
        use_gtk = cfg.get("voice.ui.use_gtk4", True)
        if use_gtk:
            orb_path = os.path.expanduser("~/Schreibtisch/Work-OS/40_Products/Vox-Voice/frontend/orb/orb.py")
            if os.path.exists(orb_path):
                print_status("Launching GTK4 Layer Shell Orb...")
                orb_ui._gtk_process = subprocess.Popen(
                    [get_ui_python(), orb_path, "--ws", "ws://127.0.0.1:7777/ws/events", "--cmd", "ws://127.0.0.1:7777/ws/command"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    env=get_ui_env()
                )
            else:
                use_gtk = False
        
        if not use_gtk:
            print_status("Starting tkinter fallback UI...")
            orb_thread = threading.Thread(target=orb_ui.run, daemon=True, name="orb-ui")
            orb_thread.start()
            
        orb_ui._ready.wait(timeout=3)

    orb_ui.set_state("loading")

    try:
        recorder = AudioRecorder(cfg, level_callback=orb_ui.set_audio_level)
        stt = STTEngine(cfg)
        print_status(f"VOX Dictation Mode | STT: {model}")
    except Exception as e:
        print(f"\033[91mInit Error:\033[0m {e}")
        sys.exit(1)

    orb_ui.set_state("idle")
    print_status("🎤 Press [Right Ctrl] to dictate | Ctrl+C = Quit")
    
    key_queue: queue.Queue = queue.Queue()
    shutdown = threading.Event()
    start_evdev_listener(key_queue, shutdown)

    while True:
        try:
            orb_ui.set_state("idle")
            key_queue.get()  # block until first keypress
            time.sleep(0.1)  # Debounce delay
            while not key_queue.empty():
                try:
                    key_queue.get_nowait()
                except queue.Empty:
                    pass
            
            orb_ui.set_state("listening")
            audio_data = recorder.record_toggle(
                key_queue, 
                stt_engine=stt, 
                transcript_callback=orb_ui.set_transcript
            )

            if audio_data is None:
                continue

            orb_ui.set_state("thinking")
            user_text = stt.transcribe(audio_data)

            if not user_text or not user_text.strip():
                orb_ui.set_state("idle")
                continue

            orb_ui.set_transcript(user_text)
            insert_text(user_text, mode=cfg.INSERT_MODE)
            print_status(f"Inserted: {user_text}")
            
            orb_ui.set_response("[Inserted into active window]")
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            shutdown.set()
            orb_ui.stop()
            print("\nGoodbye.")
            break
        except Exception as e:
            print(f"Loop Error: {e}")

@cli.command("transcribe")
@click.argument("audio_file")
@click.option("--respond", is_flag=True, help="Send transcript to Gemini and speak response.")
@click.option("--model", default="large-v3-turbo", help="Whisper model.")
def transcribe_cmd(audio_file, respond, model):
    """Transcribe an audio file."""
    cfg = Config()
    cfg.update_from_args(model=model)

    if not os.path.exists(audio_file):
        print(f"File not found: {audio_file}")
        sys.exit(1)

    data, fs = sf.read(audio_file)
    if data.ndim > 1: data = data[:, 0]

    import numpy as np
    if data.dtype != np.float32: data = data.astype(np.float32)
    if fs != 16000:
        try:
            import librosa
            data = librosa.resample(data, orig_sr=fs, target_sr=16000)
        except ImportError:
            print("librosa not available for resampling — audio may be at wrong rate")

    print_status("Transcribing...")
    stt = STTEngine(cfg)
    text = stt.transcribe(data)

    if not text:
        print_status("(nothing transcribed)")
        return

    print_user(text)

    if respond:
        session = SessionManager(cfg)
        llm = GeminiLLM(cfg)
        tts_engine = TTSEngine(cfg)
        
        # Initialize Managers
        audit_log = AuditLogger(cfg)
        perm_mgr = PermissionManager(cfg)
        skill_mgr = SkillManager(cfg)
        router = Router(cfg, permissions=perm_mgr, audit=audit_log)
        
        managers = {
            "audit": audit_log,
            "permissions": perm_mgr,
            "skills": skill_mgr,
            "router": router
        }
        
        orb_ui = VoxOrb(cfg)
        orb_ui.enabled = False
        process_turn(text, session, llm, tts_engine, orb_ui, cfg, managers)


@cli.command()
@click.argument("output_file", default="tests/data/sample.wav")
def record_test(output_file):
    """Record a 5-second test audio file for STT benchmarking."""
    cfg = Config()
    recorder = AudioRecorder(cfg)

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    audio = recorder.record_fixed(duration_s=5)
    sf.write(output_file, audio, cfg.SAMPLE_RATE)
    print(f"Saved test audio to {output_file}")


@cli.command()
@click.option("--force", is_flag=True, help="Kill EVERYTHING including the dashboard/web UI.")
def kill(force):
    """Drastically terminate all VOX processes and zombies."""
    import os
    import signal
    import subprocess
    
    print_status(f"VOX PURGE: Terminating components (Force={force})...")
    
    my_pid = os.getpid()
    
    # Core engine patterns (PAUSCHAL)
    patterns = [
        "wandavoice",
        "frontend/orb/orb.py",
        "pw-record",
        "mcc_server"
    ]
    
    # If --force is passed, we also destroy the web dashboard server
    if force:
        patterns.append("http.server 5173")
    else:
        print_status("Dashboard preserved. Use 'vox kill --force' to kill it.")
        
    # 1. KILL CORE PATTERNS
    for pattern in patterns:
        try:
            pids = subprocess.check_output(["pgrep", "-f", pattern]).decode().split()
            for pid in pids:
                if int(pid) != my_pid:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"  [X] Terminated {pattern} (PID {pid})")
                    except ProcessLookupError:
                        pass
        except subprocess.CalledProcessError:
            pass

    # 2. PRECISION KILL FOR GEMINI (ONLY WANDA SUBPROCESSES)
    try:
        all_gemini_pids = subprocess.check_output(["pgrep", "-f", "gemini"]).decode().split()
        for pid in all_gemini_pids:
            if int(pid) == my_pid: continue
            try:
                with open(f"/proc/{pid}/cmdline", "rb") as f:
                    cmdline = f.read().decode().replace('\0', ' ')
                if ".runtime/gemini_home" in cmdline or "--output-format stream-json" in cmdline:
                    os.kill(int(pid), signal.SIGKILL)
                    print(f"  [X] Terminated WANDA LLM Subprocess (PID {pid})")
            except (ProcessLookupError, FileNotFoundError):
                continue
    except subprocess.CalledProcessError:
        pass
            
    print_status("System purged. All zombies cleared.")
            
    print_status("System purged. All zombies cleared.")


import re

# ─── Helpers ───────────────────────────────────────────────────────────────

def process_turn(user_text, session, llm, tts_engine, orb_ui, cfg, managers, lt=None):
    """
    Main Orchestrator: Decision -> Action/Generation -> Output.
    managers: dict containing 'router', 'skills', 'audit', 'permissions'
    """
    from wandavoice.utils import LatencyTracker, print_debug, print_say, print_show
    if lt is None:
        lt = LatencyTracker()
    
    session.add_turn("user", user_text)
    
    # 1. Router Decision
    lt.start("Router_Decision")
    # Determine runtime options from config defaults
    rt_options = RuntimeOptions(
        target=cfg.TARGET,
        insert_mode=cfg.INSERT_MODE,
        tts_mode=cfg.TTS_MODE,
        safe_mode=False # We are in dev mode
    )
    
    decision = managers['router'].route_text(user_text, rt_options)
    lt.stop("Router_Decision")

    # 2. Execution Path
    if decision.target_used == "insert":
        orb_ui.set_state("thinking")
        lt.start("OS_Insert")
        insert_text(user_text, mode=rt_options.insert_mode)
        lt.stop("OS_Insert")
        print_say("[Inserted into active window]")
        print(lt.format_report())
        orb_ui.set_response(f"[Inserted: {user_text[:30]}...]")
        time.sleep(0.5) 
        orb_ui.set_state("idle")
        return

    # Check for Skills (Intent-based)
    if "führe aus" in user_text.lower() or "shell:" in user_text.lower():
        orb_ui.set_state("working")
        lt.start("Skill_Execution")
        # Extract command (very basic for now)
        cmd = user_text.lower().replace("führe aus", "").replace("shell:", "").strip()
        result = managers['skills'].run_skill("shell", command=cmd)
        lt.stop("Skill_Execution")
        
        managers['audit'].log("skill_execution", {"skill": "shell", "command": cmd, "result": result[:100]})
        
        feedback = f"Befehl ausgeführt. Ergebnis: {result[:50]}..."
        print_show(result)
        print_say(feedback)
        tts_engine.speak(feedback)
        tts_engine.wait()
        print(lt.format_report())
        return

    # 3. Default: LLM Streaming Generation
    orb_ui.set_state("thinking")
    print_status("Streaming response...")
    
    full_response = ""
    spoken_buffer = ""
    show_buffer = ""
    
    is_say = False
    is_show = False
    first_byte = True
    
    lt.start("LLM_TTFB") 
    lt.start("LLM_Total")

    for chunk in llm.generate_stream(user_text, session.get_history()):
        if first_byte:
            lt.stop("LLM_TTFB")
            first_byte = False
            orb_ui.set_state("speaking")
            lt.start("TTS_TTFA")

        full_response += chunk
        
        if "SAY:" in chunk: is_say = True; is_show = False
        if "SHOW:" in chunk: is_say = False; is_show = True
        
        if is_say:
            clean_chunk = chunk.replace("SAY:", "").strip()
            spoken_buffer += clean_chunk
            if any(punct in clean_chunk for punct in [".", "!", "?", "\n"]):
                parts = re.split(r'(?<=[.!?\n])', spoken_buffer)
                if len(parts) > 1:
                    to_speak = "".join(parts[:-1]).strip()
                    if to_speak:
                        if "TTS_TTFA" in lt.start_times and lt.start_times["TTS_TTFA"] > 0:
                            tts_engine.speak(to_speak)
                            lt.stop("TTS_TTFA")
                            lt.start_times["TTS_TTFA"] = 0 
                        else:
                            tts_engine.speak(to_speak)
                    spoken_buffer = parts[-1]
        
        if is_show:
            clean_chunk = chunk.replace("SHOW:", "").strip()
            show_buffer += clean_chunk
            orb_ui.set_response(f"{show_buffer[:50]}...")

    if spoken_buffer.strip():
        tts_engine.speak(spoken_buffer.strip())
        if "TTS_TTFA" in lt.start_times and lt.start_times["TTS_TTFA"] > 0:
            lt.stop("TTS_TTFA")

    lt.stop("LLM_Total")
    
    # 4. Final Skill Execution (Intent-based)
    if "SKILL:" in full_response:
        import re
        skill_match = re.search(r"SKILL:\s*(\w+)\((.*?)\)", full_response, re.DOTALL | re.IGNORECASE)
        if skill_match:
            name = skill_match.group(1).strip()
            args_str = skill_match.group(2).strip()
            try:
                kwargs = {}
                for pair in re.findall(r"(\w+)\s*=\s*['\"](.*?)['\"]", args_str, re.DOTALL):
                    kwargs[pair[0]] = pair[1]
                
                print_status(f"Executing Skill: {name}({kwargs})")
                skill_result = managers['skills'].run_skill(name, **kwargs)
                full_response += f"\n\n### Skill Result: {name}\n{skill_result}"
                
            except Exception as e:
                print_status(f"Skill Parse Error: {e}")
                full_response += f"\n\n> Skill Error: {e}"

    say, show = llm.parse_response(full_response)
    session.add_turn("assistant", f"SAY: {say} SHOW: {show}")
    
    if show: print_show(show)
    print_say(say)
    
    tts_engine.wait()
    
    print(lt.format_report())
    from wandavoice import mcc_server
    mcc_server.broadcast("latency_stats", lt.get_summary())


def main():
    cli()


if __name__ == "__main__":
    main()
