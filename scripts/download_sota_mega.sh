#!/bin/bash
set -e
MODEL_BASE="$HOME/.wanda/models"
mkdir -p "$MODEL_BASE"

echo "🚀 Starting MEGA SOTA Download (High-Quality Models only)..."

# 1. XTTS v2 (ca. 2.4GB)
echo "--- Downloading XTTS v2 (The Human King) ---"
mkdir -p "$MODEL_BASE/xtts_v2"
hf download coqui/XTTS-v2 --local-dir "$MODEL_BASE/xtts_v2"

# 2. Orpheus 3B (ca. 6GB)
echo "--- Downloading Orpheus 3B (The Smart Voice) ---"
mkdir -p "$MODEL_BASE/orpheus"
hf download deepinfra/orpheus-3b --local-dir "$MODEL_BASE/orpheus"

# 3. Qwen2.5-TTS (1.7B version)
echo "--- Downloading Qwen2.5-TTS (The Precision Expert) ---"
mkdir -p "$MODEL_BASE/qwen3"
hf download Qwen/Qwen2.5-TTS-3B --local-dir "$MODEL_BASE/qwen3"

# 4. Fish-Speech (S1-mini/Full)
echo "--- Downloading Fish-Speech S1 ---"
mkdir -p "$MODEL_BASE/fish"
hf download fishaudio/fish-speech-1.5 --local-dir "$MODEL_BASE/fish"

echo "✅ All High-End Models queued/downloaded."
