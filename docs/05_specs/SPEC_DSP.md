# DSP Spec (AEC/NS/AGC)

## MVP path
Use PipeWire Pulse module echo-cancel (WebRTC) for headset/speaker modes.
- Options include `aec_method` and `aec_args`.
  Ref: https://docs.pipewire.org/page_pulse_module_echo_cancel.html

## Production path (per session logging)
Run WebRTC AudioProcessing inside the engine.
- Rust: sonora (WebRTC AP in pure Rust). Ref: https://github.com/dignifiedquire/sonora
- Rust: webrtc-audio-processing wrapper. Ref: https://docs.rs/crate/webrtc-audio-processing/latest

## MCC panel must show
- mode: headset/speakers
- AEC on/off + aggressiveness
- NS level/profile
- AGC on/off + target level
- echo likelihood meter
- “test loop”: play TTS, measure mic leak, log AEC effectiveness
- live `dsp_state` events
