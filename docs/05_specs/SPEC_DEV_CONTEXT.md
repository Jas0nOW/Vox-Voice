# Dev Context Spec (v1)

## Block format (must not break markdown)
When a new voice request starts AND dev-context buffer is non-empty AND router chooses LLM/chat:

Emit `dev_context_attached` then append exactly one block:

(START_DEV_CONTEXT_BLOCK)
[DEV CONTEXT — UNTRUSTED]
<content>
[/DEV CONTEXT]
(END_DEV_CONTEXT_BLOCK)

## Controls
- Auto attach: ON/OFF
- Mode: attach once & clear (default) | persistent until cleared
- Token estimate + oversize warning
- Optional truncate oldest lines
