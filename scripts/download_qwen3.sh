#!/bin/bash
set -e
MODEL_BASE="$HOME/.wanda/models"
mkdir -p "$MODEL_BASE"

echo "🚀 Starting MEGA SOTA Download (Qwen3-TTS Special Edition)..."

# 1. Qwen3-TTS 1.7B VoiceDesign (Jan/Feb 2026 SOTA)
echo "--- Downloading Qwen3-TTS 1.7B VoiceDesign ---"
mkdir -p "$MODEL_BASE/qwen3"
hf download Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign --local-dir "$MODEL_BASE/qwen3"

echo "✅ Qwen3-TTS Models downloaded."
