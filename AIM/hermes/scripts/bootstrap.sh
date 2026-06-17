#!/bin/bash
# bootstrap.sh — Hermes self-study trigger
#
# Runs ONCE on first container start. Waits for Hermes to be healthy,
# then sends a self-study prompt via the chat API.
# Hermes explores all tools, skills, and API endpoints, then writes
# /opt/data/.bootstrapped to signal completion.
#
# Subsequent starts: checks for .bootstrapped and skips.

set -euo pipefail

HERMES_HOME="${HERMES_HOME:-/opt/data}"
BOOTSTRAP_FLAG="${HERMES_HOME}/.bootstrapped"
API_KEY="${HERMES_API_KEY:-hermes-secret-key}"
BOOTSTRAP_MD="/opt/hermes/skills/aim/BOOTSTRAP.md"

# ── Skip if already bootstrapped ──────────────────────────────────────
if [ -f "$BOOTSTRAP_FLAG" ]; then
    echo "[bootstrap] Already bootstrapped at $(cat "$BOOTSTRAP_FLAG"). Skipping."
    exit 0
fi

if [ ! -f "$BOOTSTRAP_MD" ]; then
    echo "[bootstrap] ERROR: BOOTSTRAP.md not found at $BOOTSTRAP_MD" >&2
    exit 1
fi

echo "[bootstrap] Starting self-study sequence..."

# ── Wait for Hermes to be healthy ─────────────────────────────────────
MAX_WAIT=60
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "[bootstrap] Hermes is healthy after ${WAITED}s"
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo "[bootstrap] ERROR: Hermes did not become healthy within ${MAX_WAIT}s" >&2
    exit 1
fi

# ── Read bootstrap instructions ───────────────────────────────────────
BOOTSTRAP_PROMPT=$(cat "$BOOTSTRAP_MD")

# ── Send self-study prompt ────────────────────────────────────────────
# Use a dedicated bootstrap session ID
BOOTSTRAP_SESSION="bootstrap-$(date +%s)"

echo "[bootstrap] Sending self-study prompt (session: $BOOTSTRAP_SESSION)..."

RESPONSE=$(curl -sf -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "X-Client-Mode: ADMIN" \
    -d "$(python3 -c "
import json, sys
prompt = sys.stdin.read()
print(json.dumps({
    'message': 'Выполни протокол самообучения из BOOTSTRAP.md. Изучи все инструменты, скиллы, API и Docker-окружение. Запиши результаты в learnings.md.',
    'session_id': '${BOOTSTRAP_SESSION}',
    'mode': 'ADMIN'
}))
" <<< "$BOOTSTRAP_PROMPT")" 2>&1) || {
    echo "[bootstrap] WARNING: curl request failed (Hermes may still be starting): $RESPONSE"
    echo "[bootstrap] Will retry on next container start."
    exit 0
}

echo "[bootstrap] Response: $(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reply','')[:200])" 2>/dev/null || echo "(parse error)")"

# ── Wait for .bootstrapped flag ───────────────────────────────────────
echo "[bootstrap] Waiting for Hermes to complete self-study..."
MAX_STUDY=300  # 5 minutes max for self-study
STUDIED=0
while [ $STUDIED -lt $MAX_STUDY ]; do
    if [ -f "$BOOTSTRAP_FLAG" ]; then
        echo "[bootstrap] Self-study complete! Flag created at $(cat "$BOOTSTRAP_FLAG")"
        exit 0
    fi
    sleep 5
    STUDIED=$((STUDIED + 5))
done

echo "[bootstrap] WARNING: Self-study did not complete within ${MAX_STUDY}s. Hermes may need a manual ADMIN message."
echo "[bootstrap] Removing flag lock to allow retry on next start."
exit 0
