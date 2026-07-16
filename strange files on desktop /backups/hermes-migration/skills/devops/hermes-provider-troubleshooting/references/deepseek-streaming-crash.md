# DeepSeek Streaming Crash — 2026-06-19

## Симптом

```
deepseek stream drop (RemoteProtocolError) after 1.5s — reconnecting, retry N/3
```

Повторяется 3 раза, затем:

```
⚠️ Provider authentication failed. Check the configured credentials; raw provider details are in the gateway logs.
```

## Причина

DeepSeek API (`https://api.deepseek.com/v1`) рвёт стриминговые HTTP-соединения через 1-2 секунды после начала ответа. Это транспортная проблема, не ключ и не модель.

**Важно:** эта ошибка выглядит как «аутентификация не прошла» для пользователя, но на самом деле ключ валиден.

## Диагностика

Прямой тест API (не-стриминг) работает:

```bash
curl -s -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}],"max_tokens":5}'
```

Если зависает — проблема в ключе/доступе. Если отвечает — проблема только в стриминге.

## Исправление

1. **Переключиться на OpenRouter** — DeepSeek через OpenRouter стримится нормально:
   ```
   /m openrouter deepseek/deepseek-chat
   ```

2. **Отключить стриминг для DeepSeek** — патч в `run_agent.py:8206`:
   ```python
   # stream=True → stream=False
   ```
   ⚠️ Патч слетает при рестарте контейнера.

3. **Прямой DeepSeek без стриминга** — если модель `deepseek-chat` (не `deepseek-reasoner`), можно попробовать `/m deepseek deepseek-chat` — результат может варьироваться в зависимости от версии Hermes.

## Наблюдения

- `deepseek-reasoner` — это reasoning-модель, склонна к долгим ответам и разрывам.
- `deepseek-chat` — обычная чат-модель, стабильнее.
- Проблема не в .env — ключ DEEPSEEK_API_KEY живой.
- Проблема не в конфиге — секция deepseek провайдера корректна.
- Единственный 100% рабочий путь — через OpenRouter.
