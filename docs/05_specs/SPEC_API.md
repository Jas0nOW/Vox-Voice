# API Spec (WebSocket)

## WS: /ws/events  (engine → UI)
Text frames: `EventEnvelope` JSON.

## WS: /ws/command (UI → engine)
Text frames: `Command` JSON:
```json
{ "type": "stop", "session_id": "<optional>", "payload": {} }
```

Minimal command set:
- `start_sim`
- `stop`
- `set_mute` { on: true|false }
- `set_sleep` { on: true|false }
- `set_profile` { vad: "command"|"chat" }
- `set_dsp` { aec_on, ns_level, agc_on, ... }
- `set_dev_context` { mode: "attach_once"|"persistent", auto: true|false, content: "..." }
