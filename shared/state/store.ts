/* ============================================================
   WANDA Shared State — Observable Store
   Minimal reactive store; no external deps.
   Can be used in React (via useSyncExternalStore) or vanilla JS.
   ============================================================ */

import type { AppState, RoutingMode, ConsoleMode, OrbState } from './types';

const DEFAULT_STATE: AppState = {
  routingMode:  'GEMINI',
  consoleMode:  'cli',
  orbState:     'SLEEPING',
  sessionId:    null,
  latencies:    [],
  session: {
    status:        'idle',
    backend:       'gemini_cli',
    model:         'auto',
    profile:       'auto',
    startTime:     null,
    restartReason: null,
    restartCount:  0,
  },
};

type Listener = (state: AppState) => void;

class WandaStore {
  private _state: AppState = structuredClone(DEFAULT_STATE);
  private _listeners: Set<Listener> = new Set();

  /** Read current state snapshot */
  getState(): Readonly<AppState> { return this._state; }

  /** Subscribe to state changes; returns unsubscribe function */
  subscribe(listener: Listener): () => void {
    this._listeners.add(listener);
    return () => this._listeners.delete(listener);
  }

  /** Merge partial update and notify listeners */
  private _update(partial: Partial<AppState>): void {
    this._state = { ...this._state, ...partial };
    this._listeners.forEach(fn => fn(this._state));
  }

  // ── Domain actions ──────────────────────────────────────────

  setRoutingMode(mode: RoutingMode): void {
    this._update({ routingMode: mode });
  }

  setConsoleMode(mode: ConsoleMode): void {
    this._update({ consoleMode: mode });
  }

  setOrbState(state: OrbState): void {
    this._update({ orbState: state });
  }

  setSessionId(id: string): void {
    this._update({ sessionId: id });
  }

  pushLatency(ms: number): void {
    const next = [...this._state.latencies, ms];
    if (next.length > 200) next.shift();
    this._update({ latencies: next });
  }

  // ── Session Manager actions ──────────────────────────────────

  sessionEnsureRunning(config: Partial<AppState['session']> = {}): void {
    const current = this._state.session;
    const next: AppState['session'] = {
      ...current,
      ...config,
      status: 'running',
      startTime: current.startTime ?? Date.now(),
    };
    this._update({ session: next });
  }

  sessionRestart(reason: string): void {
    const current = this._state.session;
    this._update({
      session: {
        ...current,
        status:        'restarting',
        restartReason: reason,
        restartCount:  current.restartCount + 1,
      },
    });
    // Async: mark running after restart completes
    setTimeout(() => {
      this._update({
        session: {
          ...this._state.session,
          status:    'running',
          startTime: Date.now(),
        },
      });
    }, 400);
  }

  sessionStopped(): void {
    this._update({
      session: {
        ...this._state.session,
        status:    'idle',
        startTime: null,
      },
    });
  }

  sessionSwitchModel(model: string): void {
    // No restart required for model switch within same backend
    this._update({
      session: { ...this._state.session, model },
    });
  }

  reset(): void {
    this._state = structuredClone(DEFAULT_STATE);
    this._listeners.forEach(fn => fn(this._state));
  }
}

export const store = new WandaStore();
export type { AppState };

// ─── React adapter (useSyncExternalStore) ─────────────────────
// Usage in React components:
//   import { useStore } from '../state/store';
//   const { routingMode, orbState } = useStore();

import { useSyncExternalStore } from 'react';

export function useStore(): Readonly<AppState> {
  return useSyncExternalStore(
    store.subscribe.bind(store),
    store.getState.bind(store),
  );
}
