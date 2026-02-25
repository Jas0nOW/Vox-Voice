# Developer Guide

## Core rules
- No component may emit an event without `session_id`.
- Every stage must be cancellable and emit `cancel_done`.
- Traces must be valid for Perfetto import (nested spans per track).

## How to add a new adapter
1) Define capability + healthcheck + cancel(session_id)
2) Emit:
   - *_start / *_chunk / *_stop
   - errors via error_raised
3) Record artifacts in CAS and reference from manifest

## Debug workflow
- Reproduce → capture run → mark golden → replay in CI
- If regression:
  - diff transcripts
  - diff router decisions
  - compare stage timings
