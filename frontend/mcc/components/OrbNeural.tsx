/* ============================================================
   OrbNeural — React Component
   Central Neural Orb/Oval with routing mode toggle & state animation.
   Requires: shared/state/store, shared/state/types
   ============================================================ */

import React, { useCallback, useEffect, useRef } from 'react';
import { store, useStore }   from '../../shared/state/store';
import type { OrbState }     from '../../shared/state/types';

const COLORS = {
  primary:   '#00F0FF',
  secondary: '#D600FF',
};

const ORB_STATE_LABEL: Record<OrbState, string> = {
  SLEEPING:      'Sleeping',
  WAKE_DETECTED: 'Wake Detected',
  LISTENING:     'Listening',
  THINKING:      'Thinking…',
  SPEAKING:      'Speaking',
  MUTED:         'Muted',
  ERROR:         'Error',
};

export function OrbNeural() {
  const { routingMode, orbState } = useStore();
  const orbRef = useRef<HTMLDivElement>(null);

  const isGemini       = routingMode === 'GEMINI';
  const accentColor    = isGemini ? COLORS.primary : COLORS.secondary;
  const isAnimating    = orbState === 'LISTENING' || orbState === 'SPEAKING';

  const handleClick = useCallback(() => {
    const next = store.getState().routingMode === 'GEMINI' ? 'WINDOW_INSERT' : 'GEMINI';
    store.setRoutingMode(next);
    // Emit neural signals (if NeuralField instance is available via window)
    if (typeof window !== 'undefined' && (window as any).neuralSignal) {
      const color = next === 'GEMINI' ? COLORS.primary : COLORS.secondary;
      (window as any).neuralSignal(color);
    }
  }, []);

  // CSS for dynamic glow based on state
  const dynamicStyle: React.CSSProperties = {
    borderColor: accentColor,
    boxShadow:   `0 0 ${isAnimating ? 60 : 36}px ${accentColor}${isAnimating ? 'cc' : '88'}, inset 0 0 30px ${accentColor}18`,
  };

  return (
    <div className="orb-container">
      <div className="orb-wrapper">
        <div
          ref={orbRef}
          className={`orb ${isGemini ? '' : 'window-insert-mode'} ${
            orbState === 'LISTENING' ? 'listening' : ''
          } ${orbState === 'SPEAKING' ? 'speaking' : ''}`}
          style={dynamicStyle}
          onClick={handleClick}
          title="Click to toggle routing mode (Gemini ↔ Window Insert)"
          role="button"
          aria-label={`Routing: ${routingMode}. State: ${orbState}. Click to toggle.`}
        >
          <span className="orb-label" style={{ color: accentColor, textShadow: `0 0 8px ${accentColor}` }}>
            WANDA
          </span>
        </div>
      </div>

      <div className="orb-state-label">
        State: <strong>{ORB_STATE_LABEL[orbState]}</strong>
      </div>

      <div
        className="orb-mode-label"
        style={{ color: accentColor }}
      >
        {isGemini ? '⬡ GEMINI MODE' : '⬡ WINDOW INSERT'}
      </div>
    </div>
  );
}
