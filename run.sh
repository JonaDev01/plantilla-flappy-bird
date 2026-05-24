#!/usr/bin/env bash
# ─── Plantilla FlappyBird — Lanzador Linux / Raspberry Pi ──────────────
# chmod +x run.sh && ./run.sh
set -e
cd "$(dirname "$0")"
python3 src/main.py
