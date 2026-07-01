#!/usr/bin/env bash
# check-server-sync.sh — Detect drift between local repo and production server
#
# Запуск: ./scripts/check-server-sync.sh
#
# Что делает:
#   1. Получает md5 всех .py файлов из /opt/hermes/app/ с сервера aim-hermes
#   2. Получает md5 локальных файлов из AIM/hermes/app/
#   3. Выводит отчёт: IDENTICAL / DIFFERENT / ONLY LOCAL / ONLY SERVER
#   4. Сохраняет полный отчёт в /tmp/server-sync-<timestamp>.txt
#
# Exit code: 0 если всё синхронизировано, 1 если есть drift.

LOCAL_ROOT="/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/app"
SERVER_CONTAINER="aim-hermes"
SERVER_PATH="/opt/hermes/app"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT="/tmp/server-sync-${TIMESTAMP}.txt"

echo "🔄 Syncing server vs local..."
echo "   Local:  $LOCAL_ROOT"
echo "   Server: $SERVER_CONTAINER:$SERVER_PATH"
echo ""

# 1. Получить серверные md5
echo "📥 Collecting server md5..."
ssh aim 'docker exec '"$SERVER_CONTAINER"' sh -c "cd '"$SERVER_PATH"' && find . -name \"*.py\" -not -path \"*/__pycache__/*\" | sort | while read f; do md5sum \"\$f\"; done"' 2>/dev/null > /tmp/server_md5_raw.txt
# Convert "./path" → "path" in output
sed 's|  \./|  |' /tmp/server_md5_raw.txt > /tmp/server_md5_full.txt

SERVER_COUNT=$(grep -c . /tmp/server_md5_full.txt || echo 0)
echo "   Server files: $SERVER_COUNT"

# 2. Получить локальные md5
echo "📥 Collecting local md5..."
(
  cd "$LOCAL_ROOT"
  for f in $(find . -name '*.py' -not -path '*/__pycache__/*' | sort); do
    md5 -q "$f" | tr -d '\n'
    echo "  ${f#./}"
  done
) > /tmp/local_md5_full.txt

LOCAL_COUNT=$(wc -l < /tmp/local_md5_full.txt)
echo "   Local files:  $LOCAL_COUNT"
echo ""

# 3. Сравнить через Python
echo "📊 Comparing..."
echo ""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/_compare_md5.py" 2>&1 | tee "$REPORT"
RESULT=${PIPESTATUS[0]}

echo ""
echo "💾 Full report saved to: $REPORT"

# Cleanup
rm -f /tmp/server_md5_full.txt /tmp/local_md5_full.txt /tmp/server_md5_raw.txt

exit $RESULT
