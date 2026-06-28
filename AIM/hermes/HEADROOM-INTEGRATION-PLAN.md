# HeadroomGuard Integration Plan

**Дата:** 2026-06-28 03:11 МСК
**Цель:** Интеграция HeadroomGuard как компрессора контекста для экономии токенов

## Что такое HeadroomGuard

HeadroomGuard — это **компрессор контекста** (не роутер провайдеров):
- Сжимает промпты на 60-95% перед отправкой в LLM
- Работает как прокси-сервер между приложением и LLM API
- Сохраняет качество ответов при значительном снижении стоимости
- Поддерживает CCR (Cached Context Retrieval) — LLM может запросить оригинал если нужно

## Текущая архитектура Hermes

```
Next.js Frontend → FastAPI (main.py) → agent_wrapper.py → AIAgent → z.ai API
                                                                   ↓
                                                              glm-5 model
```

**Текущие переменные окружения:**
- `OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4`
- `LLM_MODEL=glm-5`
- `OMNIROUTE_AUTH=6fd916373bd7462499481201277a7ad0.aCqG4YQTsePka6tI`
- `DEEPSEEK_API_KEY=sk-37839c50424c4d37b0c2a071eb3d5e55` (для теста)

## Целевая архитектура

```
Next.js Frontend → FastAPI → agent_wrapper.py → AIAgent → HeadroomGuard Proxy → z.ai API
                                                              ↓                    ↓
                                                         компрессия              glm-5
                                                         60-95%
```

**HeadroomGuard будет:**
1. Принимать запросы на `localhost:8787` (proxy mode)
2. Компрессировать промпты (SmartCrusher для JSON, CodeCompressor для кода, Kompress-base для текста)
3. Проксировать в z.ai API
4. Возвращать ответы обратно

## Deployment Strategy

### Phase 1: Local Testing (на MacBook)

1. ✅ Установить HeadroomGuard в venv (в процессе)
2. ⏳ Запустить локальный прокси: `headroom proxy --port 8787`
3. ⏳ Настроить переменные для теста:
   ```bash
   export OMNIROUTE_URL=http://localhost:8787/v1
   export HEADROOM_TARGET_URL=https://api.z.ai/api/coding/paas/v4
   ```
4. ⏳ Протестировать через curl или Python-клиент
5. ⏳ Измерить компрессию на реальных промптах SOUL.md (104 KB)

### Phase 2: Docker Integration (на сервере aim)

**Вариант A: Sidecar контейнер** (рекомендуется)
```yaml
# docker-compose.yml
services:
  aim-hermes:
    environment:
      - OMNIROUTE_URL=http://headroom-proxy:8787/v1
    depends_on:
      - headroom-proxy

  headroom-proxy:
    image: ghcr.io/chopratejas/headroom:latest
    ports:
      - "8787:8787"
    environment:
      - HEADROOM_TARGET_URL=https://api.z.ai/api/coding/paas/v4
      - HEADROOM_TARGET_AUTH=${OMNIROUTE_AUTH}
    command: headroom proxy --port 8787 --host 0.0.0.0
```

**Вариант B: В том же контейнере**
- Добавить HeadroomGuard в `requirements.txt`
- Запустить прокси в `entrypoint.sh` перед uvicorn
- Минус: усложнение Dockerfile, сложнее отладка

### Phase 3: DeepSeek Fallback (опционально)

HeadroomGuard **не умеет** выбирать между провайдерами. Для fallback нужен отдельный роутер.

**Опции:**
1. **LiteLLM Router** (уже в зависимостях):
   ```python
   from litellm import Router

   router = Router(
       model_list=[
           {"model_name": "glm-5", "litellm_params": {"model": "openai/glm-5", "api_base": "http://localhost:8787/v1"}},
           {"model_name": "deepseek-fallback", "litellm_params": {"model": "deepseek/deepseek-chat", "api_key": DEEPSEEK_API_KEY}},
       ],
       fallbacks=[{"glm-5": ["deepseek-fallback"]}],
   )
   ```

2. **Самописный роутер** (20 строк в agent_wrapper.py):
   ```python
   def _call_llm_with_fallback(messages):
       try:
           return openai_client.chat.completions.create(
               model="glm-5",
               messages=messages,
               base_url="http://localhost:8787/v1",  # через HeadroomGuard
           )
       except Exception as e:
           logger.warning("z.ai failed: %s, falling back to DeepSeek", e)
           return openai_client.chat.completions.create(
               model="deepseek-chat",
               messages=messages,
               api_key=DEEPSEEK_API_KEY,
               base_url="https://api.deepseek.com",
           )
   ```

## Риски и Mitigation

| Риск | Вероятность | Mitigation |
|------|-------------|------------|
| HeadroomGuard ломает tool calling | Средняя | Отключить компрессию для tool_calls: `HEADROOM_COMPRESS_TOOLS=false` |
| Латенси увеличивается | Низкая | Компрессия быстрая (<100ms), но можно замерить с `HEADROOM_STATS=true` |
| z.ai не понимает сжатые промпты | Низкая | HeadroomGuard сохраняет OpenAI-совместимый формат |
| DeepSeek дороже z.ai | Высокая | Это известно, fallback только для теста до 30 июня |

## Success Metrics

- ✅ **Токены сэкономлены:** 60-95% на входящих промптах
- ✅ **Качество сохранено:** Hermes генерирует отчёты той же полноты
- ✅ **Латенси приемлемая:** <200ms overhead на компрессию
- ✅ **Стабильность:** Нет ошибок 500 от HeadroomGuard за 24 часа

## Rollback Plan

1. Остановить `headroom-proxy` контейнер
2. Вернуть `OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4`
3. Перезапустить `aim-hermes`
4. Всё работает как раньше (без компрессии)

## Next Steps

1. ⏳ Дождаться установки HeadroomGuard на локальной машине
2. ⏳ Запустить локальный прокси и протестировать с SOUL.md
3. ⏳ Измерить компрессию и латенси
4. ⏳ Создать Docker-образ с HeadroomGuard для сервера
5. ⏳ Задеплоить sidecar контейнер на сервер
6. ⏳ Переключить Hermes на прокси
7. ⏳ Мониторить метрики 24 часа

## References

- HeadroomGuard README: `/tmp/headroom/README.md`
- HeadroomGuard pyproject.toml: `/tmp/headroom/pyproject.toml`
- Hermes agent_wrapper.py: `AIM/hermes/app/agent_wrapper.py`
- Current z.ai config: `OMNIROUTE_URL=https://api.z.ai/api/coding/paas/v4`
