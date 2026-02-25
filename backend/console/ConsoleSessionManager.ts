/* ============================================================
   WANDA — ConsoleSessionManager
   Manages the persistent Gemini CLI / Ollama process lifecycle.

   Design invariants:
   - ensureRunning() is IDEMPOTENT — call it freely; it only acts
     when the session state actually needs to change.
   - applySettings() restarts ONLY affected services.
   - switchModel() within the same backend: NO restart.
   - All restarts emit an event with restart_reason.
   ============================================================ */

import { EventEmitter } from 'events';
import { spawn, ChildProcess } from 'child_process';

export type LLMBackend  = 'gemini_cli' | 'ollama';
export type LLMProfile  = 'auto' | 'fast' | 'reasoning';

export interface SessionConfig {
  backend:      LLMBackend;
  profile:      LLMProfile;
  model?:       string;            // Ollama model name or Gemini model flag
  cwd?:         string;            // working directory for bridge process
  rulesFile?:   string;            // bridge-specific rules file path
  isolatedHome?: boolean;          // use isolated HOME for bridge
}

export interface SessionStatus {
  running:       boolean;
  backend:       LLMBackend;
  profile:       LLMProfile;
  model:         string;
  pid:           number | null;
  startedAt:     number | null;    // unix ms
  restartCount:  number;
  lastRestart:   string | null;    // restart reason
  uptimeMs:      number;
}

// Restart reasons (for audit log + MCC display)
type RestartReason =
  | 'initial_start'
  | 'backend_switch'
  | 'settings_apply'
  | 'manual'
  | 'watchdog'
  | 'crash';

const GEMINI_COMMANDS: Record<LLMProfile, string[]> = {
  auto:      ['gemini'],
  fast:      ['gemini', '--model', 'gemini-3-flash-preview'],
  reasoning: ['gemini', '--model', 'gemini-3-pro-preview'],
};

function ollamaCommand(model: string): string[] {
  return ['ollama', 'run', model];
}

export class ConsoleSessionManager extends EventEmitter {
  private _config:       SessionConfig | null = null;
  private _proc:         ChildProcess | null  = null;
  private _status:       'idle' | 'running' | 'restarting' = 'idle';
  private _startedAt:    number | null = null;
  private _restartCount: number = 0;
  private _lastRestart:  string | null = null;

  // ── Public API ───────────────────────────────────────────────

  /**
   * Idempotent: ensure a session matching `desiredConfig` is running.
   * - If nothing is running → start fresh.
   * - If backend changed → stop + start new session.
   * - If only model/profile changed → apply without restart.
   */
  async ensureRunning(desiredConfig: SessionConfig): Promise<void> {
    if (this._status === 'idle') {
      // Nothing running — start fresh
      await this._start(desiredConfig, 'initial_start');
      return;
    }

    if (this._status === 'restarting') {
      // Restart in progress — queue the config for after restart
      this.once('started', () => this.ensureRunning(desiredConfig));
      return;
    }

    // Running — check what changed
    const current = this._config!;
    const backendChanged = desiredConfig.backend !== current.backend;

    if (backendChanged) {
      // Backend switch requires full restart
      await this._restart(desiredConfig, 'backend_switch');
    } else {
      // Only model/profile changed — apply in-session, no restart
      this._config = { ...current, ...desiredConfig };
      this.emit('config_updated', this._config);
      this.emit('log', `[CSM] Config updated in-session (no restart): ${desiredConfig.profile}`);
    }
  }

  /**
   * Apply settings changes. Restarts only if required.
   */
  async applySettings(next: Partial<SessionConfig>): Promise<void> {
    if (!this._config || this._status === 'idle') {
      if (next.backend) {
        await this.ensureRunning({ backend: next.backend, profile: next.profile ?? 'auto' });
      }
      return;
    }

    const merged: SessionConfig = { ...this._config, ...next };
    const needsRestart = next.backend && next.backend !== this._config.backend;

    if (needsRestart) {
      await this._restart(merged, 'settings_apply');
    } else {
      this._config = merged;
      this.emit('config_updated', this._config);
      this.emit('log', '[CSM] Settings applied in-session (no restart)');
    }
  }

  /**
   * Switch model within same backend session — NO restart.
   * e.g. auto → fast: just changes the command args for next invocation.
   */
  async switchModel(profile: LLMProfile, model?: string): Promise<void> {
    if (!this._config) return;

    const current = this._config;

    // Same backend: apply without restart
    this._config = { ...current, profile, model: model ?? current.model };
    this.emit('model_switched', { from: current.profile, to: profile });
    this.emit('log', `[CSM] Model switched: ${current.profile} → ${profile} (session preserved)`);
  }

  /** Force a clean restart with reason logged */
  async forceRestart(reason: RestartReason = 'manual'): Promise<void> {
    if (!this._config) {
      this.emit('log', '[CSM] forceRestart called but no config — ignored');
      return;
    }
    await this._restart(this._config, reason);
  }

  /** Stop the session cleanly */
  async stop(): Promise<void> {
    await this._stopProc();
    this._status = 'idle';
    this._startedAt = null;
    this.emit('stopped', { reason: 'manual' });
  }

  /** Current status snapshot */
  getStatus(): SessionStatus {
    return {
      running:      this._status === 'running',
      backend:      this._config?.backend ?? 'gemini_cli',
      profile:      this._config?.profile ?? 'auto',
      model:        this._config?.model ?? 'auto',
      pid:          this._proc?.pid ?? null,
      startedAt:    this._startedAt,
      restartCount: this._restartCount,
      lastRestart:  this._lastRestart,
      uptimeMs:     this._startedAt ? Date.now() - this._startedAt : 0,
    };
  }

  // ── Private Methods ──────────────────────────────────────────

  private async _start(config: SessionConfig, reason: RestartReason): Promise<void> {
    this._config = config;
    this._status = 'running';
    this._startedAt = Date.now();
    this._lastRestart = reason;
    this._restartCount++;

    const cmd = this._buildCommand(config);
    this.emit('log', `[CSM] Starting: ${cmd.join(' ')} (reason: ${reason})`);

    try {
      this._proc = spawn(cmd[0], cmd.slice(1), {
        cwd:   config.cwd   ?? process.cwd(),
        env:   this._buildEnv(config),
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      this._proc.stdout?.on('data', (d: Buffer) => {
        this.emit('bridge_output', d.toString());
      });
      this._proc.stderr?.on('data', (d: Buffer) => {
        this.emit('bridge_error', d.toString());
      });
      this._proc.on('exit', (code, sig) => {
        const was = this._status;
        if (was === 'running') {
          // Unexpected exit → trigger watchdog restart
          this.emit('log', `[CSM] Bridge exited unexpectedly (code=${code}, sig=${sig}) — watchdog restart`);
          this._status = 'idle';
          this._restart(config, 'crash').catch(() => {});
        }
      });

      this.emit('started', this.getStatus());
      this.emit('log', `[CSM] Bridge started (pid=${this._proc.pid})`);

    } catch (err: unknown) {
      this._status = 'idle';
      this.emit('log', `[CSM] Failed to start bridge: ${(err as Error).message}`);
      this.emit('start_failed', err);
    }
  }

  private async _restart(config: SessionConfig, reason: RestartReason): Promise<void> {
    this._status = 'restarting';
    this.emit('log', `[CSM] Restarting: ${reason}`);
    this.emit('restarting', { reason });

    await this._stopProc();
    await this._start(config, reason);
  }

  private async _stopProc(): Promise<void> {
    if (!this._proc) return;
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        this._proc?.kill('SIGKILL');
        resolve();
      }, 3000);

      this._proc!.once('exit', () => {
        clearTimeout(timeout);
        this._proc = null;
        resolve();
      });

      this._proc!.kill('SIGTERM');
    });
  }

  private _buildCommand(config: SessionConfig): string[] {
    if (config.backend === 'gemini_cli') {
      const cmd = [...GEMINI_COMMANDS[config.profile ?? 'auto']];
      if (config.rulesFile) cmd.push('--rules', config.rulesFile);
      return cmd;
    }
    // ollama
    return ollamaCommand(config.model ?? 'llama3.1:8b-instruct');
  }

  private _buildEnv(config: SessionConfig): NodeJS.ProcessEnv {
    const env = { ...process.env };
    if (config.isolatedHome) {
      // Isolated HOME prevents bridge from reading user's real config
      env['HOME'] = `/tmp/wanda-bridge-${Date.now()}`;
    }
    return env;
  }
}

// ─── Singleton export ──────────────────────────────────────────
export const sessionManager = new ConsoleSessionManager();
