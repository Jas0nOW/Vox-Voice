/* ============================================================
   DevContextPanel — React Component
   Multi-tab Dev Context buffer + Window Insert mode.
   Auto-attach, token estimate, neural signal on attach.
   ============================================================ */

import React, { useState, useCallback, useRef } from 'react';
import { useStore } from '../../shared/state/store';

type TabId = 'Error' | 'Code' | 'Paths' | 'Terminal' | 'Notes';
const TABS: TabId[] = ['Error', 'Code', 'Paths', 'Terminal', 'Notes'];

interface DevContextPanelProps {
  onSendCmd: (type: string, payload?: Record<string, unknown>) => void;
  showToast: (msg: string, variant?: string) => void;
}

function tokenEstimate(text: string): number {
  return Math.ceil(text.length / 4);
}

export function DevContextPanel({ onSendCmd, showToast }: DevContextPanelProps) {
  const { routingMode } = useStore();

  const [activeTab, setActiveTab]     = useState<TabId>('Error');
  const [text, setText]               = useState('');
  const [autoAttach, setAutoAttach]   = useState(true);
  const [mode, setMode]               = useState<'once' | 'persistent'>('once');
  const [windowInsert, setWindowInsert] = useState('');

  const textareaRef    = useRef<HTMLTextAreaElement>(null);
  const isWindowInsert = routingMode === 'WINDOW_INSERT';

  const tokens = tokenEstimate(text);
  const warn   = tokens > 2000;

  const handleAttach = useCallback(() => {
    if (!text.trim()) { showToast('Dev context: nothing to attach', 'warn'); return; }
    onSendCmd('set_dev_context', { text, auto_attach: true, mode: 'once' });
    showToast('⚡ Dev context attached (once)', 'secondary');
    if (typeof window !== 'undefined' && (window as any).neuralSignal) {
      (window as any).neuralSignal('#D600FF');
    }
    if (mode === 'once') setText('');
  }, [text, mode, onSendCmd, showToast]);

  const handleSend = useCallback(() => {
    onSendCmd('set_dev_context', { text, auto_attach: autoAttach, mode });
    showToast('Dev context sent to engine');
  }, [text, autoAttach, mode, onSendCmd, showToast]);

  const handleClear = useCallback(() => {
    setText('');
    onSendCmd('set_dev_context', { text: '', auto_attach: autoAttach, mode });
    showToast('Dev context cleared');
  }, [autoAttach, mode, onSendCmd, showToast]);

  const handleWindowInsertAttach = useCallback(() => {
    if (!windowInsert.trim()) { showToast('Window Insert: nothing to attach', 'warn'); return; }
    onSendCmd('set_dev_context', { text: windowInsert, auto_attach: true, mode: 'once' });
    showToast('⬡ Window Insert attached', 'secondary');
    if (typeof window !== 'undefined' && (window as any).neuralSignal) {
      (window as any).neuralSignal('#D600FF');
    }
    setWindowInsert('');
  }, [windowInsert, onSendCmd, showToast]);

  return (
    <section className="panel" id="panel-devctx">
      <h2>Dev Context <span style={{ fontSize: 11, fontWeight: 400, color: '#5a6a8a' }}>(UNTRUSTED)</span></h2>

      <div className="card secondary-card">
        {/* Controls row */}
        <div className="row">
          <label className="inline">
            <input
              type="checkbox"
              checked={autoAttach}
              onChange={e => {
                setAutoAttach(e.target.checked);
                onSendCmd('set_dev_context', { text, auto_attach: e.target.checked, mode });
              }}
            />
            <span style={{ fontSize: 12 }}>Auto-attach</span>
          </label>

          <label className="inline">
            <span className="k" style={{ fontSize: 11, color: '#5a6a8a' }}>Mode</span>
            <select
              value={mode}
              onChange={e => setMode(e.target.value as 'once' | 'persistent')}
            >
              <option value="once">Attach once + clear</option>
              <option value="persistent">Persistent</option>
            </select>
          </label>

          <div className={`pill${warn ? ' warn' : ''}`}>
            <span className="k">Tokens</span>
            <span className="v" style={warn ? { color: '#ffd700' } : {}}>{tokens}</span>
          </div>
          {warn && <span style={{ fontSize: 10, color: '#ffd700' }}>⚠ Large context</span>}
        </div>

        {/* Tabs */}
        <div className="row" style={{ marginTop: 10, gap: 4 }}>
          {TABS.map(tab => (
            <button
              key={tab}
              className={`devtab${activeTab === tab ? ' active-toggle' : ''}`}
              onClick={() => { setActiveTab(tab); textareaRef.current?.focus(); }}
              style={{ fontSize: 11, padding: '4px 10px' }}
            >
              {tab}
            </button>
          ))}
        </div>

        <textarea
          ref={textareaRef}
          className="textarea mono"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder={`Paste ${activeTab.toLowerCase()} content here…\nEngine wraps as: (START_DEV_CONTEXT_BLOCK)…(END_DEV_CONTEXT_BLOCK)`}
          rows={8}
        />

        {/* Action buttons */}
        <div className="row" style={{ marginTop: 8 }}>
          <button onClick={handleClear}>Clear</button>
          <button
            onClick={handleAttach}
            style={{ borderColor: 'rgba(214,0,255,0.4)', color: '#D600FF' }}
          >
            ⚡ Attach
          </button>
          <button onClick={handleSend}>Send to Engine</button>
        </div>

        <p className="muted" style={{ fontSize: 11, marginTop: 6 }}>
          Block marker: <span className="mono">(START_DEV_CONTEXT_BLOCK)…(END_DEV_CONTEXT_BLOCK)</span>
        </p>
      </div>

      {/* Window Insert panel — visible only in WINDOW_INSERT routing mode */}
      {isWindowInsert && (
        <div className="card" style={{ borderColor: 'rgba(214,0,255,0.3)' }}>
          <h3 style={{ color: '#D600FF' }}>Window Insert Mode</h3>
          <p className="muted" style={{ fontSize: 11, marginBottom: 8 }}>
            Active: text/code/error pasted here is attached to next voice request.
          </p>
          <textarea
            className="textarea mono"
            value={windowInsert}
            onChange={e => setWindowInsert(e.target.value)}
            placeholder="Text / code / file path to insert into next request…"
            rows={4}
          />
          <div className="row" style={{ marginTop: 6 }}>
            <button
              onClick={handleWindowInsertAttach}
              style={{ borderColor: 'rgba(214,0,255,0.4)', color: '#D600FF' }}
            >
              ⬡ Attach to Next Request
            </button>
            <button onClick={() => setWindowInsert('')}>Clear</button>
          </div>
        </div>
      )}
    </section>
  );
}
