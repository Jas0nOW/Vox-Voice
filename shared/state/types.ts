/* ============================================================
   WANDA Shared State — Type Definitions
   Single source of truth for all modes, events, payloads.
   ============================================================ */

// ─── Routing Mode ────────────────────────────────────────────
/** What happens when voice/text is submitted */
export type RoutingMode =
  | 'GEMINI'         // Route to Gemini CLI LLM (default)
  | 'WINDOW_INSERT'; // Append to Dev Context / Window Insert buffer

// ─── Console Mode ────────────────────────────────────────────
/** Which pipeline stages are active */
export type ConsoleMode =
  | 'cli'          // Full Console + LLM routing + TTS active
  | 'simple_stt';  // STT pipeline only, raw transcript output, no LLM loop

// ─── Orb FSM States ──────────────────────────────────────────
export type OrbState =
  | 'SLEEPING'
  | 'WAKE_DETECTED'
  | 'LISTENING'
  | 'THINKING'
  | 'SPEAKING'
  | 'MUTED'
  | 'ERROR';

// ─── LLM Profiles ────────────────────────────────────────────
export type LLMProfile = 'auto' | 'fast' | 'reasoning';
export type LLMBackend = 'gemini_cli' | 'ollama';

// ─── Console Session State ───────────────────────────────────
export interface ConsoleSessionState {
  status:        'idle' | 'running' | 'restarting';
  backend:       LLMBackend;
  model:         string;
  profile:       LLMProfile;
  startTime:     number | null;   // unix ms
  restartReason: string | null;
  restartCount:  number;
}

// ─── VAD Profiles ────────────────────────────────────────────
export interface VADProfile {
  name:                'command' | 'chat';
  min_speech_ms:       number;
  end_silence_ms:      number;
  continue_window_ms:  number;
}

export const VAD_PROFILES: Record<string, VADProfile> = {
  command: { name: 'command', min_speech_ms: 150, end_silence_ms: 350,  continue_window_ms: 750  },
  chat:    { name: 'chat',    min_speech_ms: 150, end_silence_ms: 600,  continue_window_ms: 1100 },
};

// ─── Event Bus Schema ─────────────────────────────────────────
/** All events flowing over WebSocket / internal event bus */
export interface BaseEvent {
  schema_version: '1';
  session_id:     string;
  event_id:       string;
  timestamp:      number;        // unix ms
  component:      string;
  type:           EventType;
  payload:        Record<string, unknown>;
}

export type EventType =
  // Core pipeline
  | 'session_start' | 'session_end'
  | 'wake_detected'
  | 'vad_start' | 'vad_end'
  | 'stt_partial' | 'stt_final'
  | 'router_decision'
  | 'action_start' | 'action_end'
  | 'llm_stream_chunk' | 'llm_done'
  | 'tts_start' | 'tts_chunk' | 'tts_stop'
  | 'dev_context_attached'
  // Extended
  | 'audio_level' | 'audio_level_out'
  | 'audio_device_changed'
  | 'dsp_state'
  | 'cancel_request' | 'cancel_done'
  | 'run_manifest_written'
  | 'error_raised'
  | 'watchdog_restart'
  | 'orb_frame_stats'
  // MCC control
  | 'routing_mode_change'
  | 'console_mode_change'
  | 'dev_context_attached_manual';

// ─── Command Schema (MCC → Engine) ───────────────────────────
export interface MCCCommand {
  type:    CommandType;
  payload: Record<string, unknown>;
}

export type CommandType =
  | 'start_sim' | 'stop' | 'mute' | 'sleep'
  | 'set_llm_backend' | 'set_llm_profile' | 'set_ollama_model'
  | 'set_tts_voice' | 'set_stt_profile'
  | 'set_dev_context'
  | 'set_console_mode'
  | 'set_dsp_mode'
  | 'set_vad_profile'
  | 'watchdog_restart'
  | 'ptt_start' | 'ptt_stop'
  | 'test_barge_in'
  | 'mark_golden';

// ─── Run Manifest ─────────────────────────────────────────────
export interface RunManifest {
  schema_version: '1';
  session_id:     string;
  ts_start:       string;   // ISO-8601
  ts_end?:        string;
  blobs: {
    audio_raw_pcm?:   string;   // SHA256 hex
    audio_processed?: string;
    trace_perfetto?:  string;
    transcript_json?: string;
  };
  metadata: {
    wake_word:       string;
    console_mode:    ConsoleMode;
    routing_mode:    RoutingMode;
    latencies_ms:    Partial<Record<'stt' | 'llm_first_token' | 'tts_first_chunk', number>>;
    model_versions:  Partial<Record<'stt' | 'tts' | 'llm', string>>;
    dsp_params?:     Record<string, unknown>;
  };
}

// ─── App State (MCC frontend) ─────────────────────────────────
export interface AppState {
  routingMode:   RoutingMode;
  consoleMode:   ConsoleMode;
  orbState:      OrbState;
  sessionId:     string | null;
  latencies:     number[];
  session:       ConsoleSessionState;
}
