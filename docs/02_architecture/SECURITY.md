# Security & Hardening (v1)

## Skill policy
- allowlist: only installed + enabled skills can execute
- per-skill permission: `safe` | `confirm` | `blocked`
- confirm flows: required for risky actions (filesystem, network, window control)

## Dev context is untrusted
- treat as raw user input
- attach only inside explicit block
- never execute code from dev context
- do not auto-enable skills based on dev context

## Mute is hard
- “mute” closes capture stream at process level (not just UI toggle)
- UI state must be unambiguous

## Watchdog
- supervisor restarts components (bridge, stt, tts) with backoff
- emits `watchdog_restart` events; prevents crash loops
