/* ============================================================
   TinkerPanel — React Component
   CLI ↔ Simple STT toggle + model quick-switch.
   Ctrl+M keyboard shortcut registered globally.
   ============================================================ */

import React, { useCallback, useEffect } from 'react';
import { store, useStore }    from '../../shared/state/store';
import type { ConsoleMode, LLMProfile } from '../../shared/state/types';

type ToastFn = (msg: string, variant?: string) => void;

interface TinkerPanelProps {
  onSendCmd: (type: string, payload?: Record<string, unknown>) => void;
  showToast: ToastFn;
}

const PROFILES: { id: LLMProfile; label: string; icon: string }[] = [
  { id: 'fast',      label: 'Fast (gemini-3-flash-preview)',   icon: '⚡' },
  { id: 'reasoning', label: 'Reasoning (gemini-3-pro-preview)', icon: '🧠' },
  { id: 'auto',      label: 'Auto (gemini)',                    icon: '◎' },
];

export function TinkerPanel({ onSendCmd, showToast }: TinkerPanelProps) {
  const { consoleMode, session } = useStore();

  // ── Mode toggle ──────────────────────────────────────────────
  const setMode = useCallback((mode: ConsoleMode) => {
    store.setConsoleMode(mode);
    onSendCmd('set_console_mode', { mode });
    showToast(
      mode === 'cli'
        ? '▸ CLI Mode (Console + LLM active)'
        : '▸ Simple STT (pipeline only)',
    );
    if (typeof window !== 'undefined' && (window as any).neuralSignal) {
      (window as any).neuralSignal('#00F0FF');
    }
  }, [onSendCmd, showToast]);

  // ── Ctrl+M ──────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        const next: ConsoleMode = store.getState().consoleMode === 'cli' ? 'simple_stt' : 'cli';
        setMode(next);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [setMode]);

  // ── Profile switch ───────────────────────────────────────────
  const switchProfile = useCallback((profile: LLMProfile) => {
    store.sessionSwitchModel(profile);
    onSendCmd('set_llm_profile', { profile });
    showToast(`Model → ${profile} (session preserved)`);
    if (typeof window !== 'undefined' && (window as any).neuralSignal) {
      (window as any).neuralSignal('#00F0FF');
    }
  }, [onSendCmd, showToast]);

  return (
    <section className="panel" id="panel-tinker">
      <h2>Tinker MCC</h2>

      {/* ── Console Mode Toggle ── */}
      <div className="card secondary-card">
        <h3>Console Mode</h3>
        <div className="row" style={{ marginBottom: 10 }}>
          <div className="toggle-switch">
            <button
              className={consoleMode === 'cli' ? 'active-toggle' : ''}
              onClick={() => setMode('cli')}
            >
              CLI Mode
            </button>
            <button
              className={consoleMode === 'simple_stt' ? 'active-toggle' : ''}
              onClick={() => setMode('simple_stt')}
            >
              Simple STT
            </button>
          </div>
          <span className="shortcut-hint">
            <span className="kbd">Ctrl</span>+<span className="kbd">M</span>
          </span>
        </div>

        <div className="kv">
          <div>
            <span className="k">CLI active services</span>
            <span className="v" style={{ color: consoleMode === 'cli' ? '#00F0FF' : '#5a6a8a' }}>
              {consoleMode === 'cli' ? 'console + llm-routing + tts' : 'paused'}
            </span>
          </div>
          <div>
            <span className="k">STT active services</span>
            <span className="v" style={{ color: consoleMode === 'simple_stt' ? '#00F0FF' : '#5a6a8a' }}>
              {consoleMode === 'simple_stt' ? 'stt-pipeline only' : 'paused'}
            </span>
          </div>
        </div>

        <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
          CLI mode: full Console + LLM routing + TTS active.<br />
          Simple STT: only STT pipeline — raw transcript, no LLM loop.
        </p>
      </div>

      {/* ── Model Quick-Switch ── */}
      <div className="card secondary-card">
        <h3>Model / Profile Quick-Switch</h3>
        <div className="row">
          {PROFILES.map(p => (
            <button
              key={p.id}
              className={`profile${session.profile === p.id ? ' active-profile' : ''}`}
              onClick={() => switchProfile(p.id)}
            >
              {p.icon} {p.label}
            </button>
          ))}
        </div>
        <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
          Model switch within same backend session → <strong>no restart</strong>.<br />
          Backend switch (Gemini ↔ Ollama) → clean stop + new session.
        </p>
      </div>

      {/* ── Session Manager Controls ── */}
      <div className="card">
        <h3>Session Manager Controls</h3>
        <div className="row">
          <button onClick={() => { store.sessionEnsureRunning(); showToast('ensureRunning() called'); }}>
            ensureRunning()
          </button>
          <button onClick={() => {
            store.sessionEnsureRunning({ backend: 'gemini_cli', profile: session.profile });
            showToast('applySettings() — no restart');
          }}>
            applySettings()
          </button>
          <button
            className="danger"
            onClick={() => { store.sessionRestart('manual'); onSendCmd('watchdog_restart', { component: 'llm_bridge', reason: 'manual' }); showToast('Bridge restarting…', 'warn'); }}
          >
            Force Restart
          </button>
        </div>
        <div className="kv" style={{ marginTop: 10 }}>
          <div><span className="k">status</span><span className="v live">{session.status}</span></div>
          <div><span className="k">last restart reason</span><span className="v">{session.restartReason ?? '—'}</span></div>
          <div><span className="k">restart count</span><span className="v">{session.restartCount}</span></div>
        </div>
      </div>
    </section>
  );
}
