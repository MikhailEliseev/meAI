#!/bin/bash
# Deploy all Hermes files to production server
# Usage: ./scripts/deploy-hermes.sh

set -e
SERVER="aim"
CONTAINER="aim-hermes"
HERMES_DIR="/opt/hermes"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCAL_HERMES="$REPO_ROOT/AIM/hermes"

echo "=== Deploy Hermes to $SERVER ==="

FILES=(
  "app/main.py"
  "app/agent_wrapper.py"
  "app/pipeline/engine.py"
  "app/pipeline/phases.py"
  "app/pipeline/states.py"
  "app/pipeline/__init__.py"
  "app/tools/run_pagespeed.py"
  "app/tools/run_ci_analysis.py"
  "app/tools/find_company_financials.py"
  "app/tools/generate_html_report.py"
  "app/tools/publish_scout_report.py"
  "app/tools/session_archive.py"
  "app/tools/run_full_scout.py"
)

# Deploy each file
for f in "${FILES[@]}"; do
  echo "  📤 $f"
  scp "$LOCAL_HERMES/$f" "$SERVER:/tmp/hermes_$(basename $f)" 2>/dev/null
  ssh "$SERVER" "docker cp /tmp/hermes_$(basename $f) $CONTAINER:$HERMES_DIR/$f" 2>/dev/null
done

# Restart
echo "  🔄 Restarting $CONTAINER..."
ssh "$SERVER" "docker restart $CONTAINER" 2>/dev/null
sleep 5

# Health check
HEALTH=$(ssh "$SERVER" "docker exec $CONTAINER curl -s http://localhost:8000/health" 2>/dev/null)
echo "  ✅ Health: $(echo $HEALTH | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status","?"))' 2>/dev/null || echo '?')"

echo "=== Deploy complete ==="
