/* ============================================================
   WANDA MCC — app.js v2.0
   Neural Nexus Design · ConsoleSessionManager · RoutingMode
   ============================================================ */

'use strict';

// ─────────────────────────────────────────────────────────────
// § CONFIG
// ─────────────────────────────────────────────────────────────
const WS_EVENTS = "ws://127.0.0.1:7777/ws/events";
const WS_CMD    = "ws://127.0.0.1:7777/ws/command";

const COLORS = {
  bg:        '#05050A',
  primary:   '#00F0FF',
  secondary: '#D600FF',
  particle:  '#FFFFFF',
};

// ─────────────────────────────────────────────────────────────
// § SHARED STATE
// ─────────────────────────────────────────────────────────────
const state = {
  // Routing mode: what does the Orb/voice send to?
  routingMode: 'GEMINI',        // 'GEMINI' | 'WINDOW_INSERT'

  // Console mode: full CLI pipeline or STT-only
  consoleMode: 'cli',           // 'cli' | 'simple_stt'

  // Orb FSM state (mirrored from engine events)
  orbState: 'SLEEPING',         // SLEEPING | WAKE_DETECTED | LISTENING | THINKING | SPEAKING | MUTED | ERROR

  // Last session_id from engine
  sessionId: null,

  // Latency tracking
  latencies: [],
};

// ─────────────────────────────────────────────────────────────
// § HELPERS
// ─────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);

function setText(id, txt) {
  const el = $(id);
  if (el) el.textContent = txt;
}

function tokenEstimate(text) {
  return Math.ceil((text || '').length / 4);
}

// ─────────────────────────────────────────────────────────────
// § TOAST / HUD SYSTEM
// ─────────────────────────────────────────────────────────────
const hud = $('hud');
let toastQueue = [];
let toastBusy = false;

function showToast(msg, variant = 'info', durationMs = 2200) {
  // variant: 'info' | 'warn' | 'error' | 'secondary'
  toastQueue.push({ msg, variant, durationMs });
  if (!toastBusy) drainToastQueue();
}

function drainToastQueue() {
  if (toastQueue.length === 0) { toastBusy = false; return; }
  toastBusy = true;
  const { msg, variant, durationMs } = toastQueue.shift();

  const el = document.createElement('div');
  el.className = 'toast' + (variant !== 'info' ? ` ${variant}` : '');
  el.textContent = msg;
  hud.appendChild(el);

  setTimeout(() => {
    el.classList.add('fade-out');
    el.addEventListener('animationend', () => {
      el.remove();
      drainToastQueue();
    }, { once: true });
  }, durationMs);
}

// ─────────────────────────────────────────────────────────────
// § NEURAL CANVAS — NEURAL NEXUS RENDERER
// ─────────────────────────────────────────────────────────────
(function initNeuralField() {
  const canvas = $('neural-field');
  const ctx = canvas.getContext('2d', { alpha: false });

  let width, height;
  let particles = [];
  let signals = [];   // active neural signal pulses
  let time = 0;
  let mouse = { x: 0, y: 0 };
  let mouseActive = false;
  let _mouseIdleTimer = null;
  const PARTICLE_COUNT = 145;
  const CONNECT_DIST   = 155;
  const MOUSE_ATTRACT_DIST  = 200;
  const MOUSE_ATTRACT_FORCE = 0.00020;
  const MAX_SPEED  = 1.2;
  const NORM_SPEED = 0.5;            // settled speed after mouse idle

  function resize() {
    width  = canvas.width  = window.innerWidth;
    height = canvas.height = window.innerHeight;
    mouse.x = width / 2;
    mouse.y = height / 2;
  }

  function initParticles() {
    particles = [];
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x:    Math.random() * width,
        y:    Math.random() * height,
        vx:   (Math.random() - 0.5) * 1.0,
        vy:   (Math.random() - 0.5) * 1.0,
        size: Math.random() * 1.0 + 0.6,
      });
    }
  }

  // Emit a neural signal along a random active connection
  function emitSignal(color) {
    // Find particles that are currently connected (within CONNECT_DIST)
    const pairs = [];
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        if (dx * dx + dy * dy < CONNECT_DIST * CONNECT_DIST) {
          pairs.push([i, j]);
        }
      }
      if (pairs.length > 30) break; // enough candidates
    }
    if (pairs.length === 0) return;
    // Pick a random pair and emit signal in both directions
    const [i, j] = pairs[Math.floor(Math.random() * pairs.length)];
    const duration = 500 + Math.random() * 400; // ms
    const ts = performance.now();
    signals.push({ p1: particles[i], p2: particles[j], ts, duration, color: color || COLORS.primary });
    // Optionally a second burst in reverse
    if (Math.random() > 0.5) {
      signals.push({ p1: particles[j], p2: particles[i], ts: ts + 80, duration, color: color || COLORS.primary });
    }
  }

  // Expose globally so WS event handler can trigger pulses
  window.neuralSignal = function(color) {
    for (let k = 0; k < 3; k++) setTimeout(() => emitSignal(color), k * 90);
  };

  function render() {
    time += 0.012;
    const now = performance.now();

    // Background: near-opaque to create trail effect
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#05050A40';
    ctx.fillRect(0, 0, width, height);

    ctx.globalCompositeOperation = 'screen';

    // ── Update + draw particles ──
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // Mouse gravity — only when mouse is active AND particle isn't near a wall
      // (wall guard prevents particles getting pinned in corners by opposing forces)
      if (mouseActive) {
        const mdx = mouse.x - p.x;
        const mdy = mouse.y - p.y;
        const md2 = mdx * mdx + mdy * mdy;
        const nearWall = p.x < 8 || p.x > width - 8 || p.y < 8 || p.y > height - 8;
        if (!nearWall && md2 < MOUSE_ATTRACT_DIST * MOUSE_ATTRACT_DIST) {
          p.vx += mdx * MOUSE_ATTRACT_FORCE;
          p.vy += mdy * MOUSE_ATTRACT_FORCE;
        }
      }

      // Smooth return to NORM_SPEED after mouse idle — 0.9995/frame ≈ 10s at 60fps
      const spd = Math.hypot(p.vx, p.vy);
      if (!mouseActive && spd > NORM_SPEED) {
        p.vx *= 0.9995;
        p.vy *= 0.9995;
      }
      // Hard cap
      if (spd > MAX_SPEED) { p.vx = (p.vx / spd) * MAX_SPEED; p.vy = (p.vy / spd) * MAX_SPEED; }

      // Move + bounce walls
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > width)  { p.vx *= -1; p.x = Math.max(0, Math.min(width, p.x)); }
      if (p.y < 0 || p.y > height) { p.vy *= -1; p.y = Math.max(0, Math.min(height, p.y)); }

      // Draw particle
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.particle;
      ctx.fill();

      // Draw connections to subsequent particles
      for (let j = i + 1; j < particles.length; j++) {
        const p2 = particles[j];
        const dx = p.x - p2.x;
        const dy = p.y - p2.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          const alpha = Math.floor((1 - dist / CONNECT_DIST) * 255).toString(16).padStart(2, '0');
          const grad = ctx.createLinearGradient(p.x, p.y, p2.x, p2.y);
          grad.addColorStop(0, COLORS.primary + alpha);
          grad.addColorStop(1, COLORS.secondary + alpha);
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.strokeStyle = grad;
          ctx.lineWidth = (1 - dist / CONNECT_DIST) * 1.5;
          ctx.stroke();
        }
      }
    }

    // ── Draw signal pulses ──
    signals = signals.filter(sig => {
      const elapsed = now - sig.ts;
      if (elapsed < 0) return true; // not started yet
      const t = Math.min(elapsed / sig.duration, 1);
      if (t >= 1) return false; // done

      const x = sig.p1.x + (sig.p2.x - sig.p1.x) * t;
      const y = sig.p1.y + (sig.p2.y - sig.p1.y) * t;
      const opacity = Math.sin(t * Math.PI); // fade in + out

      ctx.beginPath();
      ctx.arc(x, y, 4 * opacity + 1, 0, Math.PI * 2);
      ctx.fillStyle = sig.color + Math.floor(opacity * 220).toString(16).padStart(2, '0');
      ctx.shadowBlur = 12;
      ctx.shadowColor = sig.color;
      ctx.fill();
      ctx.shadowBlur = 0;
      return true;
    });

    requestAnimationFrame(render);
  }

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouseActive = true;
    clearTimeout(_mouseIdleTimer);
    // Deactivate gravity 3s after mouse stops moving
    _mouseIdleTimer = setTimeout(() => { mouseActive = false; }, 3000);
  });
  window.addEventListener('resize', () => { resize(); initParticles(); });

  resize();
  initParticles();
  render();
})();

// ─────────────────────────────────────────────────────────────
// § RIPPLE EFFECT ON BUTTONS
// ─────────────────────────────────────────────────────────────
document.addEventListener('click', (e) => {
  const btn = e.target.closest('button');
  if (!btn) return;

  const rect = btn.getBoundingClientRect();
  const r = document.createElement('span');
  r.className = 'ripple-wave';
  r.style.left = (e.clientX - rect.left - 5) + 'px';
  r.style.top  = (e.clientY - rect.top  - 5) + 'px';
  btn.appendChild(r);
  r.addEventListener('animationend', () => r.remove(), { once: true });
});

// ─────────────────────────────────────────────────────────────
// § CONSOLE SESSION MANAGER (client-side state model)
// ─────────────────────────────────────────────────────────────
const CSM = (function() {
  let _status       = 'idle';  // idle | running | restarting
  let _model        = 'auto';
  let _profile      = 'auto';
  let _backend      = 'gemini_cli';
  let _startTime    = null;
  let _restartReason = null;
  let _restartCount = 0;
  let _uptimeTimer  = null;

  function _updateUI() {
    setText('csmStatus',        _status);
    setText('csmStatus2',       _status);
    setText('csmModel',         _model);
    setText('csmProfile',       _profile);
    setText('csmRestartReason', _restartReason || '—');
    setText('csmRestart2',      _restartReason || '—');
    setText('csmRestartCount',  _restartCount);
    setText('scModel', _model);
    setText('scRestart', _restartReason || '—');
  }

  function _startUptimeTimer() {
    if (_uptimeTimer) clearInterval(_uptimeTimer);
    _startTime = Date.now();
    _uptimeTimer = setInterval(() => {
      if (!_startTime) return;
      const s = Math.floor((Date.now() - _startTime) / 1000);
      const uptime = s < 60 ? `${s}s` : `${Math.floor(s/60)}m ${s%60}s`;
      setText('csmUptime', uptime);
      setText('scUptime', uptime);
    }, 1000);
  }

  function ensureRunning(config = {}) {
    // Idempotent: only act if something actually needs to change
    const newBackend  = config.backend  || _backend;
    const newModel    = config.model    || _model;
    const newProfile  = config.profile  || _profile;

    const backendChanged = newBackend !== _backend;

    if (_status === 'idle') {
      // Start fresh
      _backend = newBackend; _model = newModel; _profile = newProfile;
      _status = 'running';
      _startUptimeTimer();
      showToast(`Session started — ${_backend} / ${_model}`, 'info');
      _updateUI();
      return;
    }

    if (backendChanged) {
      // Backend switch requires full restart
      _restart('backend_switch', () => {
        _backend = newBackend; _model = newModel; _profile = newProfile;
      });
    } else {
      // Model/profile switch within same session — NO restart
      _model   = newModel;
      _profile = newProfile;
      showToast(`Model → ${_model} (no restart)`, 'info');
      _updateUI();
    }
  }

  function applySettings(next = {}) {
    // Only restart services that actually changed
    const needsRestart = (next.backend && next.backend !== _backend);
    if (needsRestart) {
      _restart('settings_apply', () => {
        if (next.backend)  _backend  = next.backend;
        if (next.model)    _model    = next.model;
        if (next.profile)  _profile  = next.profile;
      });
    } else {
      if (next.model)   _model   = next.model;
      if (next.profile) _profile = next.profile;
      showToast('Settings applied (no restart needed)', 'info');
      _updateUI();
    }
  }

  function switchModel(model) {
    // Within same backend: no restart
    _model = model;
    showToast(`Model → ${model} (session preserved)`, 'info');
    window.neuralSignal(COLORS.primary);
    _updateUI();
  }

  function _restart(reason, applyFn) {
    _status = 'restarting';
    _restartReason = reason;
    _restartCount++;
    _updateUI();
    showToast(`Restarting session: ${reason}`, 'warn');

    // Simulate async restart (real: send WS command)
    sendCmd('watchdog_restart', { component: 'llm_bridge', reason });
    setTimeout(() => {
      if (applyFn) applyFn();
      _status = 'running';
      _startUptimeTimer();
      showToast(`Session restarted — ${_backend} / ${_model}`, 'info');
      window.neuralSignal(COLORS.secondary);
      _updateUI();
    }, 400);
  }

  function forceRestart() { _restart('manual', null); }

  function markStopped() {
    _status = 'idle';
    _startTime = null;
    if (_uptimeTimer) { clearInterval(_uptimeTimer); _uptimeTimer = null; }
    setText('csmUptime', '—');
    setText('scUptime', '—');
    _updateUI();
  }

  function getStatus() { return { status: _status, model: _model, profile: _profile, backend: _backend }; }

  _updateUI();
  return { ensureRunning, applySettings, switchModel, forceRestart, markStopped, getStatus };
})();

// ─────────────────────────────────────────────────────────────
// § ROUTING MODE (Orb Toggle)
// ─────────────────────────────────────────────────────────────
function setRoutingMode(mode) {
  state.routingMode = mode;
  const isGemini = mode === 'GEMINI';

  // Mode badge (topbar)
  const badge = $('modeBadge');
  badge.textContent = isGemini ? 'GEMINI' : 'WINDOW INSERT';
  badge.className = 'mode-badge ' + (isGemini ? 'gemini' : 'window-insert');

  // Orb visual
  const orb = $('orb');
  if (isGemini) { orb.classList.remove('window-insert-mode'); }
  else          { orb.classList.add('window-insert-mode'); }

  // Orb mode label
  const modeLabel = $('orbModeLbl');
  modeLabel.textContent = isGemini ? '⬡ GEMINI MODE' : '⬡ WINDOW INSERT';
  modeLabel.style.color = isGemini ? COLORS.primary : COLORS.secondary;

  // Window insert panel visibility
  const wip = $('windowInsertPanel');
  if (wip) wip.style.display = isGemini ? 'none' : '';

  // Neural signal + toast
  const color = isGemini ? COLORS.primary : COLORS.secondary;
  const variant = isGemini ? 'info' : 'secondary';
  showToast(isGemini ? '⬡ Routing → Gemini' : '⬡ Routing → Window Insert', variant);
  window.neuralSignal(color);

  // Auto-switch console mode: WINDOW_INSERT → Simple STT (no LLM), GEMINI → CLI
  setConsoleMode(isGemini ? 'cli' : 'simple_stt');

  // Send to backend — critical: without this the engine ignores the mode change
  sendCmd('set_routing_mode', { mode });

  // Log
  logLine(`[routing] mode → ${mode}`);
  pushTimeline(`mode:${mode}`);
  logReplayEvent(`routing_mode_change`, { mode });
}

// ─────────────────────────────────────────────────────────────
// § CONSOLE MODE (CLI ↔ Simple STT)
// ─────────────────────────────────────────────────────────────
function setConsoleMode(mode) {
  state.consoleMode = mode;
  const isCLI = mode === 'cli';

  // Update all toggle buttons
  document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.classList.toggle('active-toggle', btn.dataset.mode === mode);
  });
  document.querySelectorAll('[data-tinker-mode]').forEach(btn => {
    btn.classList.toggle('active-toggle', btn.dataset.tinkerMode === mode);
  });

  // Status chip
  setText('scMode', isCLI ? 'CLI' : 'STT');

  showToast(isCLI ? '▸ CLI Mode (Console + LLM active)' : '▸ Simple STT (pipeline only)', 'info');
  window.neuralSignal(COLORS.primary);
  logLine(`[console] mode → ${mode}`);
  pushTimeline(`console:${mode}`);
  logReplayEvent('console_mode_change', { mode });

  // Send to engine
  sendCmd('set_console_mode', { mode });
}

function toggleConsoleMode() {
  setConsoleMode(state.consoleMode === 'cli' ? 'simple_stt' : 'cli');
}

// ─────────────────────────────────────────────────────────────
// § ORB STATE
// ─────────────────────────────────────────────────────────────
const ORB_STATES = ['SLEEPING','WAKE_DETECTED','LISTENING','THINKING','SPEAKING','MUTED','ERROR'];

function setOrbState(st) {
  state.orbState = st;
  const orb = $('orb');

  // Remove animation classes
  orb.classList.remove('listening', 'speaking');
  if (st === 'LISTENING')     orb.classList.add('listening');
  if (st === 'SPEAKING')      orb.classList.add('speaking');

  setText('orbStateLbl', st);
  setText('state', st);
}

// ─────────────────────────────────────────────────────────────
// § PANEL NAVIGATION
// ─────────────────────────────────────────────────────────────
function setPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.add('hidden'));
  document.querySelectorAll('.navbtn').forEach(b => b.classList.remove('active'));
  const panel = $(`panel-${name}`);
  const btn   = document.querySelector(`.navbtn[data-panel="${name}"]`);
  if (panel) panel.classList.remove('hidden');
  if (btn)   btn.classList.add('active');
}

// ─────────────────────────────────────────────────────────────
// § TIMELINE
// ─────────────────────────────────────────────────────────────
function pushTimeline(label) {
  const el = document.createElement('div');
  el.className = 'tchip fresh';
  el.textContent = label;
  $('timeline').prepend(el);
  // Fade "fresh" highlight after 2s
  setTimeout(() => el.classList.remove('fresh'), 2000);
  // Cap at 40 chips
  const chips = $('timeline').querySelectorAll('.tchip');
  if (chips.length > 40) chips[chips.length - 1].remove();
}

// ─────────────────────────────────────────────────────────────
// § LATENCY
// ─────────────────────────────────────────────────────────────
function updateLatency(ms) {
  state.latencies.push(ms);
  if (state.latencies.length > 200) state.latencies.shift();
  const sorted = [...state.latencies].sort((a, b) => a - b);
  const p = (q) => sorted.length ? sorted[Math.floor((sorted.length - 1) * q)] : null;
  const [p50, p95, p99] = [p(0.50), p(0.95), p(0.99)];
  setText('lat', `P50 ${p50 ?? '—'}ms / P95 ${p95 ?? '—'}ms / P99 ${p99 ?? '—'}ms`);
}

// ─────────────────────────────────────────────────────────────
// § LOG
// ─────────────────────────────────────────────────────────────
function logLine(s, cls = '') {
  const el = $('log');
  if (!el) return;
  const line = document.createElement('span');
  if (cls) line.className = cls;
  line.textContent = s + '\n';
  el.prepend(line);
  // Cap log at 500 lines
  const lines = el.childNodes;
  if (lines.length > 500) el.removeChild(lines[lines.length - 1]);
}

// ─────────────────────────────────────────────────────────────
// § REPLAY LOG (Debug/Replay panel)
// ─────────────────────────────────────────────────────────────
const replayEvents = [];

function logReplayEvent(type, payload = {}) {
  const ts = Date.now();
  replayEvents.push({ ts, type, payload });
  if (replayEvents.length > 100) replayEvents.shift();

  const el = $('replayLog');
  if (!el) return;
  const line = `${new Date(ts).toISOString().substring(11, 23)}  ${type}  ${JSON.stringify(payload)}\n`;
  el.textContent = line + el.textContent;
}

// ─────────────────────────────────────────────────────────────
// § CONVERSATION
// ─────────────────────────────────────────────────────────────
let lastSttEntry = null;

function addConvEntry(role, text, isPartial = false) {
  const conv = $('conv');
  if (!conv) return;

  if (isPartial) {
    // Update existing partial entry or create one
    if (lastSttEntry && lastSttEntry.classList.contains('partial')) {
      lastSttEntry.querySelector('.conv-text').textContent = text;
      return;
    }
    const entry = document.createElement('div');
    entry.className = `conv-entry ${role} partial`;
    entry.innerHTML = `<div class="conv-label">${role === 'user' ? 'YOU (partial)' : 'WANDA'}</div><div class="conv-text">${text}</div>`;
    conv.prepend(entry);
    lastSttEntry = entry;
    return;
  }

  // Finalize partial or create new
  if (lastSttEntry && lastSttEntry.classList.contains('partial') && role === 'user') {
    lastSttEntry.classList.remove('partial');
    lastSttEntry.querySelector('.conv-label').textContent = 'YOU';
    lastSttEntry.querySelector('.conv-text').textContent = text;
    lastSttEntry = null;
    return;
  }

  const entry = document.createElement('div');
  entry.className = `conv-entry ${role}`;
  entry.innerHTML = `<div class="conv-label">${role === 'user' ? 'YOU' : 'WANDA'}</div><div class="conv-text">${text}</div>`;
  conv.prepend(entry);
  lastSttEntry = null;
}

// ─────────────────────────────────────────────────────────────
// § WEB SOCKET + COMMAND
// ─────────────────────────────────────────────────────────────
let wsE, wsC;
let reconnectTimer = null;

function sendCmd(type, payload = {}) {
  if (!wsC || wsC.readyState !== WebSocket.OPEN) {
    logLine(`[cmd] not connected — dropped: ${type}`, 'log-err');
    return;
  }
  wsC.send(JSON.stringify({ type, payload }));
}

function connect() {
  if (wsE && wsE.readyState === WebSocket.OPEN) return;
  
  wsE = new WebSocket(WS_EVENTS);
  wsC = new WebSocket(WS_CMD);

  wsE.onopen = () => { 
    logLine('[events] connected', 'log-ok'); 
    showToast('Engine connected', 'info', 1600); 
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
  };
  wsC.onopen = () => { logLine('[cmd] connected', 'log-ok'); CSM.ensureRunning(); };

  wsE.onclose = () => { 
    logLine('[events] disconnected', 'log-err'); 
    showToast('Engine disconnected. Reconnecting in 3s...', 'warn'); 
    if (!reconnectTimer) reconnectTimer = setTimeout(connect, 3000);
  };
  wsC.onclose = () => { logLine('[cmd] disconnected', 'log-err'); CSM.markStopped(); };

  wsE.onerror = () => { logLine('[events] error — engine not running?', 'log-err'); };
  wsC.onerror = () => { logLine('[cmd] error', 'log-err'); };

  wsE.onmessage = (ev) => {
    let obj;
    try { obj = JSON.parse(ev.data); } catch { return; }

    const { session_id, component, type, payload = {}, timestamp } = obj;

    // Session tracking
    if (session_id && session_id !== state.sessionId) {
      state.sessionId = session_id;
      setText('sid', session_id.substring(0, 16) + '…');
    }

    // ── State machine transitions ──
    if (type === 'session_start')   setOrbState('LISTENING');
    if (type === 'wake_detected')   setOrbState('WAKE_DETECTED');
    if (type === 'vad_start')       setOrbState('LISTENING');
    if (type === 'stt_final')       setOrbState('THINKING');
    if (type === 'llm_done')        setOrbState('THINKING');
    if (type === 'tts_start')       setOrbState('SPEAKING');
    if (type === 'tts_stop')        setOrbState('SLEEPING');
    if (type === 'session_end')     setOrbState('SLEEPING');
    if (type === 'cancel_done')     setOrbState('SLEEPING');
    if (type === 'muted')           { setOrbState('MUTED');   showToast('🔇 Engine: muted', 'warn'); }
    if (type === 'sleep_ack')       { setOrbState('SLEEPING'); showToast('💤 Engine: sleeping', 'info'); }

    // ── Payload handlers ──
    if (type === 'audio_level')     { setText('micRms', (payload.rms ?? '—').toFixed ? payload.rms.toFixed(3) : payload.rms); }
    if (type === 'audio_level_out') { setText('outRms', (payload.rms ?? '—').toFixed ? payload.rms.toFixed(3) : payload.rms); }

    if (type === 'audio_device_changed') {
      setText('inDev',        payload.input        ?? '—');
      setText('outDev',       payload.output       ?? '—');
      setText('audioBackend', payload.backend      ?? '—');
      setText('sr',           payload.sample_rate_hz ?? '—');
    }

    if (type === 'dsp_state') {
      setText('aec',         payload.aec_on ? 'on' : 'off');
      setText('ns',          payload.ns_level ?? '—');
      setText('agc',         payload.agc_mode ?? '—');
      setText('echoLikely',  payload.echo_likelihood ?? '—');
      setText('echoLikely2', payload.echo_likelihood ?? '—');
    }

    if (type === 'orb_frame_stats') {
      setText('orbFps',  payload.fps ?? '—');
      setText('orbDrop', payload.dropped_frames ?? '—');
    }

    if (type === 'stt_partial') {
      addConvEntry('user', payload.text || '', true);
      const stEl = $('sttTranscript');
      if (stEl) stEl.textContent = `[partial] ${payload.text}\n` + stEl.textContent;
    }
    if (type === 'stt_final') {
      addConvEntry('user', payload.text || '');
      const stEl = $('sttTranscript');
      if (stEl) stEl.textContent = `[final]   ${payload.text}\n` + stEl.textContent;
      setText('sttConf', payload.confidence ? (payload.confidence * 100).toFixed(1) + '%' : '—');
      window.neuralSignal(COLORS.primary);
    }

    if (type === 'llm_stream_chunk') {
      $('llmStream').textContent += payload.text ?? '';
      setText('llmBackendLive', payload.backend ?? $('llmBackend').value);
    }
    if (type === 'llm_done') {
      const llmText = $('llmStream').textContent.trim();
      if (llmText) addConvEntry('ai', llmText.substring(llmText.length - 500));
      setText('llmBackendLive', payload.backend  ?? $('llmBackend').value);
      setText('llmProfileLive', payload.profile  ?? '—');
      setText('llmTotal',       payload.tokens   ? payload.tokens + ' tok' : '—');
      window.neuralSignal(COLORS.secondary);
    }

    if (type === 'tts_start') {
      // Clear LLM stream for next turn
      setTimeout(() => { if ($('llmStream')) $('llmStream').textContent = ''; }, 100);
    }

    if (type === 'router_decision') {
      setText('routerDecision', payload.decision ?? '—');
      setText('routerReason',   payload.reason   ?? '—');
    }

    if (type === 'run_manifest_written') {
      const path = payload.path ?? '—';
      const sha  = payload.trace_sha256 ?? '—';
      setText('manifestPath',  path); setText('manifestPath2',  path);
      setText('traceHash',     sha);  setText('traceHash2',     sha);
    }

    if (type === 'dev_context_attached') {
      showToast('Dev context attached to request', 'secondary');
      window.neuralSignal(COLORS.secondary);
    }

    if (type === 'cancel_request' || type === 'cancel_done') {
      showToast(`⊗ ${type === 'cancel_request' ? 'Cancelling...' : 'Pipeline cancelled'}`, 'warn');
    }

    if (type === 'error_raised') {
      showToast(`⚠ Error: ${payload.code ?? ''} [${payload.component ?? '?'}]`, 'error');
      setOrbState('ERROR');
      logLine(`[error] ${payload.code} @ ${payload.component}`, 'log-err');
    }

    if (type === 'watchdog_restart') {
      showToast(`↺ Watchdog restart: ${payload.component ?? '?'} — ${payload.reason ?? ''}`, 'warn');
    }

    if (type === 'vad_state') {
      setText('vadMinSpeech', payload.min_speech_ms ?? '—');
      setText('vadEndSilence', payload.end_silence_ms ?? '—');
      setText('vadContinue', payload.continue_window_ms ?? '—');
      logLine(`[vad] profile=${payload.profile ?? '?'} min=${payload.min_speech_ms}ms end=${payload.end_silence_ms}ms`);
    }

    if (type === 'wake_words_updated') {
      const words = payload.words ?? [];
      if (typeof renderWakeWords === 'function') renderWakeWords(words);
      logLine(`[wakeword] updated: ${words.join(', ')}`, 'log-ok');
    }

    if (type === 'skill_allowlist_updated') {
      const al = payload.allowlist ?? [];
      if (typeof renderSkills === 'function') renderSkills(al, payload.permissions ?? {});
      logLine(`[skills] allowlist updated: ${al.join(', ')}`, 'log-ok');
    }

    if (type === 'set_routing_mode') {
      logLine(`[router] mode → ${payload.mode ?? '?'}`);
    }
    if (type === 'set_console_mode') {
      logLine(`[console] mode → ${payload.mode ?? '?'}`);
    }

    // Latency (rough signal from llm_done)
    if (type === 'llm_done' && timestamp) updateLatency(1200);

    // Log + timeline + replay
    logLine(`[${component ?? '?'}] ${type}`);
    pushTimeline(type);
    logReplayEvent(type, payload);
  };
}

// ─────────────────────────────────────────────────────────────
// § CHROME TRACE EXPORT (Perfetto-compatible)
// ─────────────────────────────────────────────────────────────
function exportChromeTrace() {
  // Convert replayEvents to Perfetto Chrome JSON format
  const baseTs = replayEvents.length ? replayEvents[0].ts : Date.now();
  const events = replayEvents.map((ev, i) => ({
    name: ev.type,
    ph:   'X',                             // complete event
    ts:   (ev.ts - baseTs) * 1000,         // microseconds
    dur:  1000,                            // 1ms placeholder
    pid:  1, tid: 1,
    cat:  ev.payload.component ?? 'voice',
    args: ev.payload,
  }));
  const trace = { traceEvents: events };
  const blob = new Blob([JSON.stringify(trace, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `wanda_trace_${state.sessionId ?? 'session'}_${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
  showToast('Chrome trace exported — drop into ui.perfetto.dev', 'info');
}

// ─────────────────────────────────────────────────────────────
// § WAKE WORD MANAGER
// ─────────────────────────────────────────────────────────────
const wakeWords = ['Hey Wanda', 'Wanda'];

function renderWakeWords() {
  const list = $('wakeWordList');
  if (!list) return;
  list.innerHTML = '';
  wakeWords.forEach((word, i) => {
    const row = document.createElement('div');
    row.className = 'row ww-row';
    row.innerHTML = `<span class="ww-label">${word}</span>
      <button onclick="editWakeWord(${i})" style="padding:3px 8px;font-size:11px">Edit</button>
      <button onclick="deleteWakeWord(${i})" style="padding:3px 8px;font-size:11px;border-color:rgba(255,80,80,0.3);color:#ff6b6b">✕</button>`;
    list.appendChild(row);
  });
}
window.editWakeWord = function(i) {
  const val = prompt('Wake word:', wakeWords[i]);
  if (val && val.trim()) { wakeWords[i] = val.trim(); renderWakeWords(); sendCmd('set_wake_words', { words: wakeWords }); }
};
window.deleteWakeWord = function(i) {
  wakeWords.splice(i, 1); renderWakeWords(); sendCmd('set_wake_words', { words: wakeWords });
  showToast('Wake word removed', 'warn'); logLine(`[wake] removed word`);
};
window.addWakeWord = function() {
  const val = $('wakeWordInput')?.value?.trim();
  if (!val) { showToast('Enter a wake word first', 'warn'); return; }
  wakeWords.push(val); $('wakeWordInput').value = '';
  renderWakeWords(); sendCmd('set_wake_words', { words: wakeWords });
  showToast(`Wake word added: "${val}"`, 'info'); logLine(`[wake] added: ${val}`);
};

// ─────────────────────────────────────────────────────────────
// § SKILLS MANAGER
// ─────────────────────────────────────────────────────────────
const skills = [
  { name: 'calendar',    perm: 'safe' },
  { name: 'web_search',  perm: 'confirm' },
  { name: 'file_write',  perm: 'blocked' },
];

function renderSkills() {
  const list = $('skillsList');
  if (!list) return;
  list.innerHTML = '';
  skills.forEach((sk, i) => {
    const permColor = sk.perm === 'safe' ? '#00F0FF' : sk.perm === 'confirm' ? '#FFB800' : '#ff6b6b';
    const row = document.createElement('div');
    row.className = 'row ww-row';
    row.innerHTML = `<span class="ww-label" style="flex:1">${sk.name}</span>
      <select onchange="updateSkillPerm(${i}, this.value)" style="width:110px">
        <option value="safe"${sk.perm==='safe'?' selected':''}>✓ Safe</option>
        <option value="confirm"${sk.perm==='confirm'?' selected':''}>? Confirm</option>
        <option value="blocked"${sk.perm==='blocked'?' selected':''}>✕ Blocked</option>
      </select>
      <button onclick="deleteSkill(${i})" style="padding:3px 8px;font-size:11px;border-color:rgba(255,80,80,0.3);color:#ff6b6b">✕</button>`;
    list.appendChild(row);
  });
  sendCmd('set_skill_allowlist', { skills });
}
window.updateSkillPerm = function(i, perm) {
  skills[i].perm = perm; renderSkills();
  showToast(`Skill "${skills[i].name}" → ${perm}`, 'info'); logLine(`[skill] ${skills[i].name} → ${perm}`);
};
window.deleteSkill = function(i) {
  const name = skills[i].name; skills.splice(i, 1); renderSkills();
  showToast(`Skill removed: ${name}`, 'warn'); logLine(`[skill] removed: ${name}`);
};
window.addSkill = function() {
  const val = $('skillInput')?.value?.trim();
  if (!val) { showToast('Enter a skill name first', 'warn'); return; }
  skills.push({ name: val, perm: 'confirm' }); $('skillInput').value = '';
  renderSkills(); showToast(`Skill added: "${val}" (confirm)`, 'info'); logLine(`[skill] added: ${val}`);
};

// ─────────────────────────────────────────────────────────────
// § UI BINDINGS
// ─────────────────────────────────────────────────────────────
function bindUI() {

  // ── Nav panel switching ──
  document.querySelectorAll('.navbtn').forEach(btn => {
    btn.addEventListener('click', () => setPanel(btn.dataset.panel));
  });
  setPanel('overview');

  // ── Top-bar primary controls ──
  $('btnStart').addEventListener('click', () => {
    sendCmd('start_sim', {});
    CSM.ensureRunning();
    setOrbState('LISTENING');
    showToast('▶ Session started', 'info');
    logLine('[btn] Start → LISTENING');
  });
  $('btnStop').addEventListener('click', () => {
    sendCmd('stop', {});
    CSM.markStopped();
    setOrbState('SLEEPING');
    showToast('■ Session stopped', 'warn');
    logLine('[btn] Stop → SLEEPING');
  });
  $('btnMute').addEventListener('click', () => {
    sendCmd('mute', {});
    setOrbState('MUTED');
    showToast('🔇 Muted', 'warn');
    logLine('[btn] Mute → MUTED');
  });
  $('btnSleep').addEventListener('click', () => {
    sendCmd('sleep', {});
    setOrbState('SLEEPING');
    showToast('💤 Sleeping…', 'info');
    logLine('[btn] Sleep → SLEEPING');
  });
  $('btnRestartBridge').addEventListener('click', () => {
    CSM.forceRestart();
    logLine('[btn] Restart Bridge');
  });

  // ── Orb click → routing mode toggle ──
  $('orb').addEventListener('click', () => {
    const next = state.routingMode === 'GEMINI' ? 'WINDOW_INSERT' : 'GEMINI';
    setRoutingMode(next);
  });
  $('modeBadge').addEventListener('click', () => {
    const next = state.routingMode === 'GEMINI' ? 'WINDOW_INSERT' : 'GEMINI';
    setRoutingMode(next);
  });

  // ── CLI/STT toggle (topbar) ──
  document.querySelectorAll('[data-mode]').forEach(btn => {
    btn.addEventListener('click', () => setConsoleMode(btn.dataset.mode));
  });

  // ── CLI/STT toggle (Tinker panel) ──
  document.querySelectorAll('[data-tinker-mode]').forEach(btn => {
    btn.addEventListener('click', () => setConsoleMode(btn.dataset.tinkerMode));
  });

  // ── Ctrl+M keyboard shortcut ──
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'm') {
      e.preventDefault();
      toggleConsoleMode();
    }
  });

  // ── Shared sync helpers (keep topbar + settings panel in sync) ──
  function syncBackend(backend) {
    ['llmBackend', 'setLLMBackend'].forEach(id => { const el=$(id); if(el) el.value=backend; });
    sendCmd('set_llm_backend', { backend });
    CSM.ensureRunning({ backend });
    logLine(`[llm] backend → ${backend}`);
  }
  function syncProfile(profile) {
    document.querySelectorAll('button.profile').forEach(b =>
      b.classList.toggle('active-profile', b.dataset.profile === profile));
    ['setLLMProfile'].forEach(id => { const el=$(id); if(el) el.value=profile; });
    sendCmd('set_llm_profile', { profile });
    CSM.switchModel(profile);
    logLine(`[llm] profile → ${profile}`);
  }

  // ── LLM backend dropdowns (topbar + settings share same logic) ──
  $('llmBackend').addEventListener('change', (e) => syncBackend(e.target.value));

  // ── Profile buttons (all, including Tinker) ──
  document.querySelectorAll('button.profile').forEach(btn => {
    btn.addEventListener('click', () => syncProfile(btn.dataset.profile));
  });

  // ── Session manager buttons (Tinker) ──
  $('btnCSMEnsure').addEventListener('click', () => { CSM.ensureRunning(); showToast('ensureRunning() called', 'info'); });
  $('btnCSMApplySettings').addEventListener('click', () => {
    CSM.applySettings({
      backend: $('llmBackend').value,
      profile: 'auto',
    });
  });
  $('btnCSMRestart').addEventListener('click', () => { CSM.forceRestart(); });

  // ── Bridge restart (LLM panel) ──
  $('btnRestartBridge2')?.addEventListener('click', () => { CSM.forceRestart(); });
  $('btnClearLLMStream')?.addEventListener('click', () => { $('llmStream').textContent = ''; });

  // ── Settings panel ──
  $('btnApplyLLM').addEventListener('click', () => {
    const backend = $('setLLMBackend').value;
    const profile = $('setLLMProfile').value;
    const ollamaModel = $('setOllamaModel').value;
    syncBackend(backend);
    syncProfile(profile);
    sendCmd('set_ollama_model', { model: ollamaModel });
    CSM.applySettings({ backend, profile });
    showToast('LLM settings applied', 'info');
    pushTimeline('llm_settings_applied');
    logLine(`[settings] LLM applied: ${backend} / ${profile}`);
  });

  $('btnApplyVoice').addEventListener('click', () => {
    const ttsVoice  = $('setTTSVoice').value;
    const sttProfile = $('setSTTProfile').value;
    sendCmd('set_tts_voice',   { voice: ttsVoice });
    sendCmd('set_stt_profile', { profile: sttProfile });
    setText('ttsEngine', ttsVoice);
    setText('sttModel',  sttProfile);
    showToast('Voice settings applied', 'info');
  });

  // ── Dev Context panel ──
  $('devText').addEventListener('input', () => {
    setText('devTok', tokenEstimate($('devText').value));
  });
  $('devClear').addEventListener('click', () => {
    $('devText').value = '';
    setText('devTok', '0');
    sendCmd('set_dev_context', { text: '', auto_attach: $('devAuto').checked, mode: $('devMode').value });
    showToast('Dev context cleared', 'info');
  });
  $('devAttach').addEventListener('click', () => {
    sendCmd('set_dev_context', { text: $('devText').value, auto_attach: true, mode: 'once' });
    showToast('⚡ Dev context attached (once)', 'secondary');
    window.neuralSignal(COLORS.secondary);
    pushTimeline('dev_ctx_attached');
    logReplayEvent('dev_context_attached_manual', { chars: $('devText').value.length });
  });
  $('devSend').addEventListener('click', () => {
    sendCmd('set_dev_context', { text: $('devText').value, auto_attach: $('devAuto').checked, mode: $('devMode').value });
    showToast('Dev context sent to engine', 'info');
  });
  $('devAuto').addEventListener('change', () => {
    sendCmd('set_dev_context', { text: $('devText').value, auto_attach: $('devAuto').checked, mode: $('devMode').value });
  });
  $('devMode').addEventListener('change', () => {
    sendCmd('set_dev_context', { text: $('devText').value, auto_attach: $('devAuto').checked, mode: $('devMode').value });
  });

  // Dev context tabs
  document.querySelectorAll('.devtab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.devtab').forEach(b => b.classList.remove('active-toggle'));
      btn.classList.add('active-toggle');
      $('devText').placeholder = `Paste ${btn.dataset.tab.toLowerCase()} content here…`;
    });
  });

  // Window Insert
  $('btnWindowInsertAttach')?.addEventListener('click', () => {
    const text = $('windowInsertText').value.trim();
    if (!text) { showToast('Window Insert: nothing to attach', 'warn'); return; }
    sendCmd('set_dev_context', { text, auto_attach: true, mode: 'once' });
    showToast('⬡ Window Insert attached', 'secondary');
    window.neuralSignal(COLORS.secondary);
    $('windowInsertText').value = '';
  });
  $('btnWindowInsertClear')?.addEventListener('click', () => {
    $('windowInsertText').value = '';
  });

  // ── Conversation panel ──
  $('btnConvClear')?.addEventListener('click', () => {
    $('conv').innerHTML = '';
    showToast('Conversation cleared', 'info');
  });
  $('btnConvExport')?.addEventListener('click', () => {
    const text = Array.from($('conv').querySelectorAll('.conv-entry'))
      .map(e => `[${e.classList.contains('user') ? 'YOU' : 'WANDA'}] ${e.querySelector('.conv-text')?.textContent}`)
      .reverse().join('\n');
    navigator.clipboard.writeText(text).then(() => showToast('Conversation copied to clipboard', 'info'));
  });
  $('btnMarkGolden')?.addEventListener('click', () => {
    showToast('★ Marked as golden run', 'info');
    sendCmd('mark_golden', { session_id: state.sessionId });
  });

  // ── Debug/Replay panel ──
  $('btnExportTrace')?.addEventListener('click', exportChromeTrace);
  $('btnReplayCopy')?.addEventListener('click', () => {
    navigator.clipboard.writeText(state.sessionId ?? '').then(() => showToast('session_id copied', 'info'));
  });

  // ── Logs panel ──
  $('btnClearLog')?.addEventListener('click', () => { $('log').innerHTML = ''; });
  $('btnCopyLog')?.addEventListener('click', () => {
    navigator.clipboard.writeText($('log').textContent).then(() => showToast('Log copied', 'info'));
  });

  // ── DSP mode buttons ──
  document.querySelectorAll('[data-dsp-mode]').forEach(btn => {
    btn.addEventListener('click', () => {
      sendCmd('set_dsp_mode', { mode: btn.dataset.dspMode });
      showToast(`DSP mode → ${btn.dataset.dspMode}`, 'info');
    });
  });

  // ── VAD profile buttons ──
  document.querySelectorAll('[data-vad-profile]').forEach(btn => {
    btn.addEventListener('click', () => {
      sendCmd('set_vad_profile', { profile: btn.dataset.vadProfile });
      showToast(`VAD profile → ${btn.dataset.vadProfile}`, 'info');
    });
  });

  // ── TTS barge-in test ──
  $('btnTestBargeIn')?.addEventListener('click', () => {
    sendCmd('test_barge_in', {});
    showToast('Barge-in test started — watch latency', 'info');
  });

  // ── PTT ──
  const ptt = $('btnPTT');
  if (ptt) {
    ptt.addEventListener('mousedown', () => sendCmd('ptt_start', {}));
    ptt.addEventListener('mouseup',   () => sendCmd('ptt_stop',  {}));
  }
}

// ─────────────────────────────────────────────────────────────
// § BOOT
// ─────────────────────────────────────────────────────────────
bindUI();
connect();

renderWakeWords();
renderSkills();
logLine('[boot] WANDA MCC Neural Nexus v2 — loaded', 'log-ok');
logLine('[boot] Connecting to ws://127.0.0.1:7777 …', 'log-ok');
logLine('[boot] Tip: start backend/voice-engine to enable live data', 'log-ok');

setTimeout(() => showToast('WANDA MCC — Neural Nexus v2', 'info', 3000), 300);
setTimeout(() => showToast('Click the Orb to toggle routing mode', 'secondary', 3500), 1000);
