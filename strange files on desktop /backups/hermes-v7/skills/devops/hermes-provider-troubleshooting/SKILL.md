---
name: hermes-provider-troubleshooting
description: Diagnose and fix Hermes LLM provider failures — authentication errors, streaming drops, model-not-found, config mismatches. Covers OpenRouter, DeepSeek, Anthropic, any custom provider.
category: devops
triggers:
  - "Provider authentication failed"
  - "No LLM provider configured"
  - "stream drop"
  - "RemoteProtocolError"
  - LLM provider failure
  - provider not working
  - can't connect to model
  - hermes provider
  - model switch not working
  - /m fails
  - "провайдер не работает"
  - "ошибка аутентификации"
  - "модель не отвечает"
  - все ошибки провайдера
  - diagnostic provider
  - debug provider
  - diagnose hermes
---

# Hermes Provider Troubleshooting

Диагностика и восстановление LLM-провайдеров при сбоях аутентификации, стриминга или конфигурации.

## Архитектура

Hermes определяет провайдера через `config.yaml`:

```yaml
model:
  default: <model-name>          # модель по умолчанию
  provider: <provider-name>       # имя из секции providers ниже
  base_url: <url>                 # опционально, может быть в секции providers

providers:
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
    model_mapping:
      openai/gpt-4o-mini: openai/gpt-4o-mini
  deepseek:
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
    model_mapping:
      deepseek-reasoner: deepseek-reasoner
      deepseek-chat: deepseek-chat
```

**Ключевое правило:** `model.provider` должен точно соответствовать имени в секции `providers`. `/m openrouter ...` переключает `model.provider` на `openrouter`, но если в `providers` нет секции `openrouter` с `base_url` и `api_key` — запросы падают.

## Стандартный диагностический пайплайн

При любой жалобе «провайдер не работает»:

### Шаг 1: Проверь конфиг

```bash
cat /opt/hermes/config.yaml
```

Проверить:
- Есть ли секция `model:` с `default` и `provider`
- Есть ли секция `providers.X` где X = model.provider
- Есть ли у провайдера `base_url` (у OpenRouter — обязательно!)
- Есть ли `api_key: ${...}` ссылающийся на существующую переменную

**⚠️ Частая причина OpenRouter падений:** `base_url` отсутствует в секции `openrouter:` провайдера. OpenRouter-провайдер БЕЗ `base_url` не может маршрутизировать запросы — падает с той же ошибкой что и «Provider authentication failed».

### Шаг 2: Проверь ключи

```bash
# Показать какие ключи есть
grep -E "(_API_KEY|_TOKEN)" /opt/hermes/.env | cut -d= -f1

# Проверить что ключ читается внутри контейнера (если Docker)
docker exec hermes grep OPENROUTER_API_KEY /opt/hermes/.env
```

**⚠️ config_chmod: '0444' в config.yaml** — если секция `file_protection:` содержит `config_chmod: '0444'`, то файл config.yaml делается read-only ПОСЛЕ старта. Любые правки в config.yaml не сохранятся при перезапуске.

### Шаг 3: Прямой тест API

```bash
# OpenRouter
curl -s -X POST https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":"test"}],"max_tokens":5}'

# DeepSeek  
curl -s -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}],"max_tokens":5}'

# Проверить баланс OpenRouter
curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/auth/key
```

## Типовые паттерны ошибок

### 1. DeepSeek — RemoteProtocolError (stream drop)

**Симптом:** `deepseek stream drop (RemoteProtocolError) after 1.5s — reconnecting, retry N/3`

**Причина:** DeepSeek API (api.deepseek.com) рвёт стриминговые соединения. Это НЕ проблема ключа — это транспортная проблема.

**Диагностика:** отличить от проблем с ключом — если то же самое curl-тестирование (Шаг 3) работает, а Hermes падает, это стриминговая проблема.

**Исправление:**
1. Переключиться на другого провайдера: `/m openrouter openai/gpt-4o-mini` (если OpenRouter настроен)
2. Либо отключить стриминг для DeepSeek в коде run_agent.py

### 2. OpenRouter — не работает после /m

**Симптом:** `Provider authentication failed` при использовании `/m openrouter <model>`

**Причина (90% случаев):** в `providers:` конфига нет `openrouter:` с `base_url: https://openrouter.ai/api/v1`

**Исправление:** Добавить секцию openrouter в providers конфига:
```yaml
providers:
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
```

### 3. Любой провайдер — «No LLM provider configured»

**Симптом:** `RuntimeError: No LLM provider configured. Run hermes model to select a provider.`

**Причина:** gateway не может найти валидного провайдера — или раздел `model:` отсутствует, или `model.provider` не имеет соответствующей секции в `providers:`, или активная модель не найдена.

**Исправление:** `/m <provider> <model>` с заведомо рабочим провайдером (например, `/m openrouter openai/gpt-4o-mini`).

### 4. «Provider authentication failed» — тройной провал

**Симптом:** Три сообщения подряд: `⚠️ Provider authentication failed.`

**Причина:** Hermes ретраит неудачный запрос 3 раза, и только потом показывает ошибку. Single retry pattern: первый запрос → ошибка → ретрай 1 → ошибка → ретрай 2 → все три упали → «Provider authentication failed». 

**Важно:** Это catch-all сообщение. Реальная причина может быть:
- Неверное имя модели (например, `gpt-5.2-nanosoft` не существует)
- Drop соединения (DeepSeek стриминг)
- Неверный ключ или истёкший
- Rate limiting
- Проблема с base_url

**Всегда проверяй gateway.log и errors.log для реальной ошибки:**
```bash
cat /opt/hermes/gateway.log | tail -30
cat /opt/hermes/errors.log | tail -30
```

### 5. Сессионный оверрайд модели (/m) не живёт

**Симптом:** Смена модели через `/m` работает, но после `docker restart` или `/reset` возвращается старая модель.

**Причина:** `/m` меняет модель runtime (в памяти процесса), но НЕ в config.yaml. При рестарте config.yaml читается заново. Если config.yaml содержит config_chmod: '0444' — правки в него не сохраняются.

**Исправление:** Править config.yaml ПЕРЕД рестартом, убедившись что config_chmod не делает его read-only.

## Конфигурация провайдеров (эталон)

Готовая секция для config.yaml с обоими основными провайдерами:

```yaml
model:
  default: openai/gpt-4o-mini
  provider: openrouter
providers:
  deepseek:
    base_url: https://api.deepseek.com/v1
    api_key: ${DEEPSEEK_API_KEY}
    model_mapping:
      deepseek-reasoner: deepseek-reasoner
      deepseek-v4-pro: deepseek-chat
      deepseek-v4-flash: deepseek-chat
  openrouter:
    base_url: https://openrouter.ai/api/v1
    api_key: ${OPENROUTER_API_KEY}
    model_mapping:
      openai/gpt-4o-mini: openai/gpt-4o-mini
      openai/gpt-4o: openai/gpt-4o
      anthropic/claude-sonnet-4: anthropic/claude-sonnet-4
```

## Pitfalls

- **OpenRouter требует `base_url`.** Без него провайдер не может слать запросы. `model.base_url` НЕ заменяет `providers.openrouter.base_url`.
- **config_chmod: '0444' делает конфиг read-only после старта.** Сессионные патчи не выживают. Правь config ПОСЛЕ снятия chmod.
- **«Provider authentication failed» — это catch-all.** 3 ретрая, все упали → эта ошибка. Настоящая причина в логах.
- **Не путай провайдера и маршрутизатор.** OpenRouter — это маршрутизатор к моделям OpenAI/Anthropic/Google. Если настроить OpenRouter, модели OpenAI доступны через него, не нужен отдельный OpenAI провайдер.
- **DeepSeek стриминг нестабилен через прямой API.** RemoteProtocolError — транспортная проблема, не ключ и не модель.
- **docker exec внутри контейнера.** Чтобы тестить ключи напрямую, используй `docker exec hermes curl ...` — это bypass-нет Hermes и показывает реальный ответ API.
- **Не сохраняй ключи в навыки.** Ключи в .env, конфигурация в config.yaml. Файлы навыков public-видимы.

## Related

- `aim/aim-operations` — для проблем с AIM API (app:8000), не с LLM провайдерами
- `aim/client-onboarding-pipeline` — для пайплайна пресейла, не для диагностики провайдера
