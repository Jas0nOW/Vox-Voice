# Replay & Artifacts (Golden Runs)

## Storage model
- `cas/sha256/<hash>`: immutable blobs (audio, traces, transcripts, configs)
- `runs/<date>/<session_id>/manifest.json`: points to CAS blobs + metadata

Why: dedupe, integrity, reproducibility (CAS is a common pattern in build systems).  
Refs:
- Bazel remote caching / CAS: https://bazel.build/remote/caching
- bazel-remote CAS keyed by SHA256: https://github.com/buchgr/bazel-remote

## Manifest (minimal)
- session_id, started_at, ended_at
- config snapshot hash
- device IDs + sample rates
- model identifiers/hashes
- dsp parameters
- artifacts:
  - audio_in (pre & post DSP)
  - audio_out
  - trace.json
  - transcripts.json
  - router.json
- redaction flags + retention policy

## Golden workflow
1) MCC “Mark as Golden” → copies manifest pointer into `goldens/index.json`
2) CI runs `replay_goldens`:
   - re-run deterministic components (router, normalization)
   - compare transcripts + decisions
   - enforce perf budgets (P95 thresholds)
