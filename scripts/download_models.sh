#!/bin/bash
set -e

MODEL_BASE="$HOME/.wanda/models"
mkdir -p "$MODEL_BASE/kokoro"
mkdir -p "$MODEL_BASE/whisper"
mkdir -p "$MODEL_BASE/orpheus"

echo "🎙️ Starting SOTA Model Downloads for WANDA..."

# 1. Kokoro-82M (ONNX)
echo "--- Downloading Kokoro-82M ---"
if [ ! -f "$MODEL_BASE/kokoro/kokoro-v0_19.onnx" ]; then
    wget -L -O "$MODEL_BASE/kokoro/kokoro-v0_19.onnx" https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/kokoro-v0_19.onnx
fi
# Note: kokoro-onnx expects a voices.bin or voices.json. 
# Many implementations now use voices.bin for speed.
if [ ! -f "$MODEL_BASE/kokoro/voices.bin" ]; then
    wget -L -O "$MODEL_BASE/kokoro/voices.bin" https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices.bin
fi

echo "✅ SOTA Models directory structure prepared at $MODEL_BASE"
