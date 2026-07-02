#!/usr/bin/env bash
# switch-llm.sh — переключение LLM провайдера (DeepSeek / Z-AI / OpenRouter)
#
# Использование:
#   ./scripts/switch-llm.sh           # показать статус
#   ./scripts/switch-llm.sh deepseek  # переключить на DeepSeek
#   ./scripts/switch-llm.sh zai       # переключить на Z-AI Coding Plan (GLM-4.6)
#   ./scripts/switch-llm.sh openrouter
#
# Что делает:
#   1. Backup /opt/aim/AIM/.env.production → .env.production.bak
#   2. Обновляет LLM_* переменные в .env.production
#   3. Перезапускает aim-hermes контейнер
#   4. Проверяет health

set -euo pipefail

ENV_FILE="/opt/aim/AIM/.env.production"
HERMES_ENV_FILE="/opt/hermes-data/.env"

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ── Конфигурация провайдеров ──────────────────────────────────────────

# DeepSeek (default)
DEEPSEEK_KEY="sk-5c6a5c1063a34a0abe84d288b037bb42"
DEEPSEEK_BASE="https://api.deepseek.com"
DEEPSEEK_MODEL="deepseek-v4-pro"

# Z-AI Coding Plan (GLM-5.2 — новейшая)
ZAI_KEY="6fd916373bd7462499481201277a7ad0.aCqG4YQTsePka6tI"
ZAI_BASE="https://api.z.ai/api/coding/paas/v4"
ZAI_MODEL="glm-5.2"

# OpenRouter (если есть ключ)
OPENROUTER_KEY="${OPENROUTER_API_KEY:-}"
OPENROUTER_BASE="https://openrouter.ai/api/v1"
OPENROUTER_MODEL="anthropic/claude-sonnet-4"

# ── Функции ───────────────────────────────────────────────────────────

show_status() {
    echo "📊 Текущий LLM провайдер:"
    if ssh aim "grep -q '^LLM_BASE_URL=$DEEPSEEK_BASE' $ENV_FILE" 2>/dev/null; then
        echo -e "  ${GREEN}● DeepSeek ($DEEPSEEK_MODEL)${NC}"
    elif ssh aim "grep -q '^LLM_BASE_URL=$ZAI_BASE' $ENV_FILE" 2>/dev/null; then
        echo -e "  ${GREEN}● Z-AI Coding Plan ($ZAI_MODEL)${NC}"
    elif ssh aim "grep -q '^LLM_BASE_URL=$OPENROUTER_BASE' $ENV_FILE" 2>/dev/null; then
        echo -e "  ${GREEN}● OpenRouter ($OPENROUTER_MODEL)${NC}"
    else
        echo -e "  ${YELLOW}? Unknown${NC}"
    fi
    echo ""
    echo "Доступные провайдеры:"
    echo "  deepseek    — DeepSeek V4 Pro (default)"
    echo "  zai         — Z-AI Coding Plan (GLM-4.6, подписка)"
    echo "  openrouter  — OpenRouter (нужен OPENROUTER_API_KEY env)"
}

update_env() {
    local provider="$1"
    local key="$2"
    local base="$3"
    local model="$4"

    local COMPOSE_FILE="/opt/aim/AIM/docker-compose.yml"

    echo "📝 Updating:"
    echo "   $ENV_FILE → $provider ($model)"
    echo "   $COMPOSE_FILE → fixing hardcoded OMNIROUTE_URL"

    # Backup both
    ssh aim "cp $ENV_FILE ${ENV_FILE}.bak.$(date +%Y%m%d-%H%M%S)"
    ssh aim "cp $COMPOSE_FILE ${COMPOSE_FILE}.bak.$(date +%Y%m%d-%H%M%S)"

    # Update .env.production
    ssh aim "
        sed -i \\
            -e 's|^LLM_PROVIDER=.*|LLM_PROVIDER=custom|' \\
            -e 's|^LLM_BASE_URL=.*|LLM_BASE_URL=$base|' \\
            -e 's|^LLM_API_KEY=.*|LLM_API_KEY=$key|' \\
            -e 's|^LLM_MODEL=.*|LLM_MODEL=$model|' \\
            -e 's|^OMNIROUTE_URL=.*|OMNIROUTE_URL=$base|' \\
            -e 's|^OMNIROUTE_AUTH=.*|OMNIROUTE_AUTH=$key|' \\
            $ENV_FILE
    "

    # Update docker-compose.yml (the hardcoded OMNIROUTE_URL line)
    ssh aim "sed -i 's|OMNIROUTE_URL=https://api.deepseek.com/v1|OMNIROUTE_URL=$base|' $COMPOSE_FILE"

    # Verify
    echo "✅ .env.production:"
    ssh aim "grep -E '^LLM_MODEL|^LLM_BASE_URL|^LLM_PROVIDER|^OMNIROUTE_URL' $ENV_FILE"
    echo ""
    echo "✅ docker-compose.yml:"
    ssh aim "grep OMNIROUTE_URL $COMPOSE_FILE"
}

restart_hermes() {
    echo ""
    echo "🔄 Recreating aim-hermes (force-recreate to pick up new env)..."
    # docker restart НЕ перечитывает env_file — нужно force-recreate
    ssh aim "cd /opt/aim/AIM && docker compose up -d --force-recreate hermes"

    echo "⏳ Waiting for healthcheck (max 60s)..."
    for i in {1..60}; do
        local status=$(ssh aim "docker ps --filter name=aim-hermes --format '{{.Status}}'" 2>/dev/null || echo "?")
        if echo "$status" | grep -q "healthy"; then
            echo -e "  ${GREEN}✅ Healthy after ${i}s${NC}"
            return 0
        fi
        sleep 1
    done
    echo -e "  ${RED}❌ Health check failed${NC}"
    return 1
}

# ── Main ──────────────────────────────────────────────────────────────

case "${1:-}" in
    deepseek)
        update_env "deepseek" "$DEEPSEEK_KEY" "$DEEPSEEK_BASE" "$DEEPSEEK_MODEL"
        restart_hermes
        echo -e "${GREEN}✅ Switched to DeepSeek${NC}"
        ;;
    zai)
        update_env "zai" "$ZAI_KEY" "$ZAI_BASE" "$ZAI_MODEL"
        restart_hermes
        echo -e "${GREEN}✅ Switched to Z-AI Coding Plan ($ZAI_MODEL)${NC}"
        ;;
    openrouter)
        if [ -z "$OPENROUTER_KEY" ]; then
            echo -e "${RED}❌ OPENROUTER_API_KEY env var not set${NC}"
            exit 1
        fi
        update_env "openrouter" "$OPENROUTER_KEY" "$OPENROUTER_BASE" "$OPENROUTER_MODEL"
        restart_hermes
        echo -e "${GREEN}✅ Switched to OpenRouter${NC}"
        ;;
    status|"")
        show_status
        ;;
    *)
        echo "Usage: $0 {deepseek|zai|openrouter|status}"
        exit 1
        ;;
esac
