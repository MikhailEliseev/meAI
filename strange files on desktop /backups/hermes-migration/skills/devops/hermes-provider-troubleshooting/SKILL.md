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
grep -E "(_API_KEY|_TOKEN)" /opt/hermes/.env

# Проверить что ключ читается (в контейнере)
grep -E "OPENROUTER|DEEPSEEK|ANTHROPIC" /opt/hermes/.env | cut -d= -f1
```

**⚠️ docker exec НЕДОСТУПЕН внутри контейнера.** Если ты (агент) запускаешь `terminal()`, то ты ВНУТРИ контейнера. Docker CLI отсутствует. Для прямых тестов API используй `curl` напрямую — не через `docker exec`.

**⚠️ config_chmod: '0444' в config.yaml** — если секция `file_protection:` содержит `config_chmod: '0444'`, то файл config.yaml делается read-only ПОСЛЕ старта. Любые правки в config.yaml не сохранятся при перезапуске.

### Шаг 2.5: Проверь что config.yaml не перезаписывается при старте

**Симптом:** правишь config.yaml, но после рестарта контейнера/шлюза возвращается старая версия (например, `deepseek-reasoner`).

**Причина:** внешний скрипт (start.sh, init-скрипт, docker-entrypoint) перезаписывает config.yaml при старте.

**Диагностика:**
```bash
# Найти кто пишет в config.yaml при старте
grep -r "config.yaml" /opt/hermes/start.sh /opt/hermes/init.sh /opt/hermes/entrypoint.sh /opt/hermes/.profile /opt/hermes/.bashrc 2>/dev/null

# Или поискать в script файлах
ls -la /opt/hermes/*.sh 2>/dev/null

# Проверить время модификации — свежий файл после рестарта?
stat /opt/hermes/config.yaml
```

**Исправление:** найти скрипт, который перезаписывает config, и отредактировать ЭТОТ скрипт, а не сам config.yaml. Либо выпилить команду копирования из скрипта.

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

## Цикл-брейкер: когда ошибка повторяется 5+ раз

**Симптом:** одна и та же ошибка «Provider authentication failed» повторяется 5, 10, 50 раз подряд. Агент продолжает предлагать одни и те же диагнозы, пользователь раздражается.

**Правило:** после 5+ повторений одной и той же ошибки в одной сессии:

1. **Перестать диагностировать.** Дальнейшие попытки диагностики с теми же инструментами бесполезны — агент внутри контейнера не имеет доступа к docker, а конфиг на диске уже проверен.
2. **Выдать одну чёткую команду пользователю**, без объяснений и вариантов. Что именно сделать на хосте.
3. **Пример:** «Михаил, нужен рестарт. `/reset` не поможет. Выполни на сервере: `docker restart aim-hermes`»
4. **Не извиняться, не объяснять.** Пользователь в раздражении — нужен action, не анализ.

### 5. Сессионный оверрайд модели (/m) не живёт

**Симптом:** Смена модели через `/m` работает, но после `docker restart` или `/reset` возвращается старая модель.

**Причина:** `/m` меняет модель runtime (в памяти процесса), но НЕ в config.yaml. При рестарте config.yaml читается заново. Если config.yaml содержит config_chmod: '0444' — правки в него не сохраняются. Если внешний скрипт перезаписывает config.yaml при старте — правки тоже не живут.

**Исправление:** Править config.yaml ПЕРЕД рестартом. Если есть перезаписывающий скрипт — править скрипт, не config.yaml.

### 6. Модель не существует — проверка перед /m

**Симптом:** модель `deepseek-v4-pro`, `gpt-5.2-nanosoft` и т.д. не существуют, но были заданы в конфиге. Hermes честно пытается слать запросы и падает.

**Профилактика:** перед сменой модели через `/m`:
1. **OpenRouter:** проверить что модель существует через их API: `curl -s https://openrouter.ai/api/v1/models | grep -c "model-name"`
2. **DeepSeek:** модели называются `deepseek-chat` и `deepseek-reasoner`. Никаких `deepseek-v4-pro`, `deepseek-v4-flash`.
3. **Если есть сомнения — используй `/m openrouter/auto`** — OpenRouter сам выберет рабочую модель для заданного провайдера.
4. **Если модель неизвестна — не гадай.** Лучше спроси у пользователя точное имя или проверь через web_search каталог моделей провайдера.

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

## References

- `references/deepseek-streaming-crash.md` — подробный recipe по DeepSeek streaming drop: диагностика, тесты, исправление. Создан по следам реал-тайм дебага (2026-06-19).
