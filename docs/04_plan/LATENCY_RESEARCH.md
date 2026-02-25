# Gemini CLI Latency Research (WANDA Voice OS)

*Status: Under Investigation | Date: 2026-02-25*

## The Problem
The primary LLM backend for WANDA Voice is the `Gemini CLI`. However, on the current Pop!_OS (Cosmic) environment, the CLI exhibits extreme latency that violates the Voice OS P95 budgets (End-speech to TTS < 1500ms):
1. **Startup Latency:** Typing `gemini` in the terminal takes ~10 seconds before the prompt appears or the process fully initializes.
2. **Inference/Network Latency:** After submitting a prompt, the CLI takes an additional ~15 seconds to "think" before emitting the first token.

Total latency: ~25 seconds. This renders real-time voice conversation impossible. For comparison, local models (Ollama) or other cloud CLIs (Claude, Codex) respond almost instantly.

## Potential Root Causes (Hypotheses) & Findings

### 1. Node.js Boot & Module Loading
- **Test:** `time gemini --version`
- **Result:** ~1.2 seconds.
- **Conclusion:** While 1.2s is slow for a CLI just to print a version, it does not explain the full 10s startup delay. The CLI itself is heavy, but not 10s heavy on pure boot.

### 2. Node.js DNS Resolution (IPv6 Blackholing)
- **Test:** Direct Node.js `dns.resolve4` and `dns.resolve6` to `generativelanguage.googleapis.com`, followed by a TCP connection test.
- **Result:** Both IPv4 and IPv6 resolve in ~20ms. Direct TCP connection over IPv6 establishes in ~24ms.
- **Conclusion:** **DISPROVED.** The OS network stack, ISP, and IPv6 routing are perfectly healthy and extremely fast.

### 3. State Locks / Recursive Context Loading (The "Inception" Delay)
- **Hypothesis:** When running `gemini` inside a complex workspace (or recursively inside another Gemini CLI session), the CLI spends massive amounts of time reading local context (`GEMINI.md`, directory trees, `.gitignore` parsing) or waiting on SQLite/JSON state locks (`~/.gemini/state.json` or history files). 
- **Evidence:** If the CLI tries to parse a massive project directory synchronously before sending the prompt, or if two CLI instances fight for a lock file, this easily causes 10s+ delays.

### 4. API Endpoint Routing & Server-Side "Thinking"
- **Hypothesis:** The remaining 15 seconds of delay after the prompt is sent might be a combination of the sheer size of the context payload being uploaded to the API, and the Gemini model "thinking" (if reasoning profiles are active).

## Mitigation Strategy for WANDA Voice

Since we have proven that the network itself is fast (24ms ping to Google), the latency is entirely localized within the CLI's pre-processing, context gathering, and API payload generation.

1. **Persistent Subprocess (The LLM Adapter):**
   We will NEVER spawn a new `gemini` process per turn. The `GeminiCLIAdapter` starts the CLI *once* in the background and keeps the `stdin`/`stdout` pipes open. This completely bypasses the 1.2s boot and any initial context-gathering delays.
   
2. **Headless Execution / Isolation:**
   When WANDA spawns the Gemini CLI, it must be spawned with an isolated home directory (`isolated_home=".runtime/gemini_home"`) or with flags that disable local directory scanning. We only want WANDA to feed it explicit context, preventing the CLI from wasting 10 seconds scanning `node_modules` or massive git histories.

3. **Tracing:**
   The `voice-engine` will emit `llm_first_token_ms` metrics to the event bus. If the delay persists in the persistent pipe, we will know it's purely API/Model reasoning latency, at which point we switch to `gemini-3-flash` (Flash models) exclusively for voice.

## Next Diagnostic Steps for the User
- Run `time gemini --version` to see pure JS startup time.
- Run `NODE_DEBUG=net,tls gemini "test"` to trace network bottlenecks.
- Temporarily disable IPv6 system-wide on Pop!_OS to see if the 15s delay vanishes.