#!/bin/bash
# ============================================================
#  setup.sh — Run this ONCE after docker-compose up
#  Purpose : Pull tinyllama model into Ollama container
# ============================================================

set -e

echo "============================================"
echo "  Qualibytes GPT — First Time Setup"
echo "============================================"

# Step 1: Start all containers
echo "[1/3] Starting all containers..."
docker-compose up -d

# Step 2: Wait for Ollama to be ready
echo "[2/3] Waiting for Ollama to be ready..."
until docker exec qualibytes-ollama ollama list > /dev/null 2>&1; do
  echo "  Ollama starting... waiting 3s"
  sleep 3
done
echo "  Ollama is ready!"

# Step 3: Pull tinyllama (only downloads once — stored in volume)
echo "[3/3] Pulling tinyllama model (~637MB)..."
echo "  This will take a few minutes on first run."
docker exec qualibytes-ollama ollama pull tinyllama

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "  Open: http://$(curl -s ifconfig.me 2>/dev/null || echo 'YOUR-SERVER-IP')"
echo "============================================"
