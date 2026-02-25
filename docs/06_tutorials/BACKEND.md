# Tutorial: Backend (voice-engine)

## 1) Run in simulation mode
```bash
cd backend/voice-engine
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
voice-engine --mode sim --ws-host 127.0.0.1 --ws-port 7777
```

## 2) What you should see
- MCC receives events via WS `/ws/events`
- `runs/<date>/<session_id>/manifest.json` written
- `runs/<date>/<session_id>/trace.json` written
- CAS blobs under `cas/sha256/<hash>`

## 3) Next step: replace sim pipeline
Replace `VoiceEngine.start_sim_session()` with real stages:
capture → dsp → wake → vad → stt → router → llm → tts → playback

Rule: every stage emits events + spans and respects CancelToken.
