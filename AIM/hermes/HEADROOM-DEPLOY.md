# HeadroomGuard Deployment Guide

**Дата:** 2026-06-28 03:12 МСК
**Цель:** Развернуть HeadroomGuard как sidecar прокси для экономии токенов

## Pre-Deploy Checklist

✅ **Подготовка завершена:**
- [x] Docker-compose конфигурация создана: `AIM/docker-compose.headroom.yml`
- [x] План интеграции документирован: `AIM/hermes/HEADROOM-INTEGRATION-PLAN.md`
- [x] Текущая конфигурация изучена (z.ai на glm-5)

⏳ **Что нужно сделать:**
- [ ] Сделать backup текущей конфигурации
- [ ] Скачать образ HeadroomGuard на сервере
- [ ] Запустить sidecar контейнер
- [ ] Переключить Hermes на прокси
- [ ] Протестировать пресейл через iamaim.ru

## Step 1: Backup Current State

```bash
# На сервере
ssh aim

# Backup docker-compose.yml
cp /opt/aim/docker-compose.yml /opt/backups/docker-compose-before-headroom-$(date +%Y%m%d-%H%M%S).yml

# Backup текущих переменных окружения Hermes
docker exec aim-hermes env > /opt/backups/hermes-env-before-headroom-$(date +%Y%m%d-%H%M%S).txt

# Backup конфигурации
docker exec aim-hermes cat /opt/data/config.yaml > /opt/backups/hermes-config-before-headroom-$(date +%Y%m%d-%H%M%S).yaml 2>/dev/null || echo "No config.yaml"
```

## Step 2: Deploy HeadroomGuard Sidecar

```bash
# Скопировать конфигурацию на сервер
scp AIM/docker-compose.headroom.yml aim:/opt/aim/

# На сервере
ssh aim
cd /opt/aim

# Скачать образ HeadroomGuard
docker pull ghcr.io/chopratejas/headroom:latest

# Запустить с обоими compose-файлами
docker-compose -f docker-compose.yml -f docker-compose.headroom.yml up -d headroom-proxy

# Проверить что прокси работает
docker logs aim-headroom-proxy --tail 50
curl http://localhost:8787/health
```

## Step 3: Reconfigure Hermes to Use Proxy

```bash
# На сервере
cd /opt/aim

# Обновить переменные окружения Hermes
docker-compose -f docker-compose.yml -f docker-compose.headroom.yml up -d aim-hermes

# Проверить что Hermes видит новый URL
docker exec aim-hermes env | grep OMNIROUTE_URL
# Должно быть: OMNIROUTE_URL=http://headroom-proxy:8787/v1

# Проверить логи Hermes
docker logs aim-hermes --tail 50
```

## Step 4: Test End-to-End

```bash
# 1. Проверить health endpoint Hermes
curl http://localhost:8000/health

# 2. Открыть https://iamaim.ru в браузере
# 3. Отправить тестовый URL клиники
# 4. Наблюдать логи обоих контейнеров

# Терминал 1: Hermes
docker logs -f aim-hermes | grep -E "(tool|compress|token)"

# Терминал 2: HeadroomGuard
docker logs -f aim-headroom-proxy | grep -E "(compress|saving|token)"
```

## Step 5: Monitor Metrics

```bash
# HeadroomGuard dashboard (если включен)
curl http://localhost:8787/dashboard

# Статистика сжатия
curl http://localhost:8787/stats | jq

# Prometheus метрики Hermes
curl http://localhost:8000/metrics | grep -E "(token|compress)"
```

## Expected Results

После деплоя HeadroomGuard должен:
- ✅ Компрессировать входящие промпты на 60-95%
- ✅ Сохранить качество ответов Hermes
- ✅ Не ломать tool calling (HEADROOM_COMPRESS_TOOLS=false)
- ✅ Добавить <200ms латенси на компрессию

**Метрики для мониторинга:**
```
Before: SOUL.md (104 KB) + user message → ~40,000 tokens → z.ai
After:  SOUL.md (104 KB) + user message → HeadroomGuard → ~8,000 tokens → z.ai
Savings: 80% tokens, 80% cost
```

## Rollback Plan

Если что-то сломалось:

```bash
# На сервере
cd /opt/aim

# Вариант 1: Остановить только прокси (Hermes упадёт в fallback)
docker-compose -f docker-compose.yml -f docker-compose.headroom.yml stop headroom-proxy

# Вариант 2: Вернуть оригинальную конфигурацию
docker-compose down aim-hermes
docker-compose -f docker-compose.yml up -d aim-hermes

# Проверить что вернулись к z.ai напрямую
docker exec aim-hermes env | grep OMNIROUTE_URL
# Должно быть: OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4

# Удалить прокси
docker-compose -f docker-compose.yml -f docker-compose.headroom.yml down headroom-proxy
docker rmi ghcr.io/chopratejas/headroom:latest
```

## Troubleshooting

### HeadroomGuard не компрессирует

**Симптом:** Логи показывают "compression skipped"

**Причины:**
1. `HEADROOM_MODE=audit` (dry-run режим)
2. Промпт слишком короткий (<1000 токенов)
3. Контент не поддаётся компрессии (уже сжат)

**Fix:**
```bash
docker exec aim-headroom-proxy env | grep HEADROOM_MODE
# Если audit → изменить на optimize в docker-compose.headroom.yml
```

### Tool calling сломался

**Симптом:** Hermes не вызывает инструменты, логи показывают JSON parse errors

**Причина:** HeadroomGuard сжал tool_calls схемы

**Fix:**
```bash
# Проверить настройку
docker exec aim-headroom-proxy env | grep HEADROOM_COMPRESS_TOOLS
# Должно быть false

# Если true → исправить в docker-compose.headroom.yml и перезапустить
docker-compose -f docker-compose.yml -f docker-compose.headroom.yml restart headroom-proxy
```

### Латенси слишком высокая

**Симптом:** Ответы приходят медленнее чем раньше (>1s overhead)

**Причина:** Компрессия больших промптов требует времени

**Mitigation:**
```bash
# Включить только лёгкую компрессию
# В docker-compose.headroom.yml добавить:
# - HEADROOM_COMPRESSION_LEVEL=fast  # fast | balanced | max
```

### z.ai отклоняет сжатые промпты

**Симптом:** 400 Bad Request от z.ai API

**Причина:** HeadroomGuard использует специфичные токены/форматы

**Fix:**
```bash
# Отключить продвинутую компрессию, только SmartCrusher
# В docker-compose.headroom.yml:
# - HEADROOM_USE_KOMPRESS=false
# - HEADROOM_USE_CODE_COMPRESSOR=false
```

## Success Criteria

Деплой считается успешным если:
1. ✅ HeadroomGuard контейнер healthy
2. ✅ Hermes подключён к прокси (OMNIROUTE_URL=http://headroom-proxy:8787/v1)
3. ✅ Тестовый пресейл завершается успешно (HTML отчёт генерируется)
4. ✅ Логи HeadroomGuard показывают compression stats >50%
5. ✅ Латенси приемлемая (<500ms overhead)
6. ✅ Нет ошибок 500 в течение 1 часа

## Next Steps After Success

1. Мониторить метрики 24 часа
2. Сравнить стоимость токенов (до/после)
3. Если стабильно → коммитнуть docker-compose.headroom.yml
4. Обновить документацию в CLAUDE.md
5. Добавить в SESSION.md отметку об интеграции HeadroomGuard

## DeepSeek Fallback (Phase 2)

HeadroomGuard только компрессирует, не выбирает провайдера. Для fallback нужен дополнительный роутер.

**Опции:**
1. **LiteLLM Router** в agent_wrapper.py (20 строк)
2. **Portkey** как отдельный sidecar
3. **Самописный if/else** с try/except

**Пока:** z.ai PRIMARY через HeadroomGuard, DeepSeek НЕ используется (только ключ в env).

## References

- HeadroomGuard README: https://github.com/chopratejas/headroom
- HeadroomGuard Docker: https://github.com/chopratejas/headroom/pkgs/container/headroom
- Integration Plan: `AIM/hermes/HEADROOM-INTEGRATION-PLAN.md`
- Current z.ai config: `OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4`
- Current model: `LLM_MODEL=glm-5`
