# План: переключение hermes-v2 в прод (blue-green, инкрементально)

## ⚠️ Стратегические допущения (т.к. ответов не было — принял по умолчанию)

Принял **безопасный инкрементальный путь**:
- **Чат на сайте** → переключаем на v2 (это ради чего работали 14-17 июля: дизайн-система, отзывы, форматтеры)
- **Telegram бот** → остаётся на v1 (v2 не имеет webhook-роутов — сломается)
- **HTML-отчёты iamaim.ru/{slug}** → остаются генерироваться через v1 (v2 не имеет HTML builder + WP publishing — это P0 gap, 1500+ строк кода)
- **Откат** → мгновенный, 1 команда nginx reload

Если хотели полную замену v1 (включая отчёты + telegram + аутентификацию) — скажите, перепишу план (объём: 2-4 недели).

---

## 📊 Краткое обоснование

v2 на коммите `ace9d62b` — рабочий Walking Skeleton для **presale-чата**: клиент шлёт URL → 4 тула параллельно → 4 секции точных данных (профиль, конкуренты, отзывы, аудит) + LLM-нарратив. Anti-hallucination 4 уровня. Это то, ради чего писали код 14-17 июля.

**Не хватает для полной замены v1**: HTML-отчёты, telegram, auth, 13-фазный pipeline. Но для чата на сайте — достаточно.

---

## 🔧 Реализация: 6 шагов

### Шаг 1. Предполётные проверки на сервере (15 мин)

SSH на сервер `aim`, проверить 3 блокера:

```bash
# 1. .env.keys — docker-compose v2 требует, файла может не быть
ssh aim "ls -la /opt/aim/AIM/.env.keys"
# Если НЕТ → создать пустой или убрать из docker-compose.yml строки 165-166

# 2. Host mount для v2 данных
ssh aim "ls -la /opt/hermes-v2-data/"
# Если НЕТ → sudo mkdir -p /opt/hermes-v2-data && sudo chown root:root /opt/hermes-v2-data

# 3. Git состояние на сервере
ssh aim "cd /opt/aim/AIM && git status && git log -1 --oneline"
```

**Действия по результатам:**
- Если `.env.keys` нет — выбрать: создать минимальный или убрать `env_file: .env.keys` из `AIM/docker-compose.yml:166`
- Если `/opt/hermes-v2-data/` нет — создать

### Шаг 2. Локальные тесты v2 (30 мин)

Перед деплоем — прогнать тесты v2 локально:

```bash
cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes-v2
# 4 теста без сети:
python -m pytest tests/test_competitors.py tests/test_session.py tests/test_key_pool.py tests/test_anti_hallucination.py -v
```

Все 4 должны PASS. Если падают — стоп, разбираться.

### Шаг 3. Подготовить конфиг nginx с разделением переменных (локально, закоммитить)

**Файл:** `AIM/deploy/nginx/iamaim.conf`

Сейчас (строка 44):
```nginx
set $hermes "hermes:8000";
```

Стало (разделить чат и telegram):
```nginx
# Чат на сайте → hermes-v2 (новая дизайн-система, отзывы, форматтеры)
set $hermes "hermes-v2:8000";
# Telegram остаётся на v1 (v2 не имеет telegram webhook'ов)
set $hermes_telegram "hermes:8000";
```

И обновить 2 location'а telegram (строки ~145, ~156):
```nginx
location = /telegram/test-webhook {
    ...
    proxy_pass http://$hermes_telegram/telegram/webhook;  # было $hermes
}
location /telegram/webhook {
    ...
    proxy_pass http://$hermes_telegram;  # было $hermes
}
```

Чат-роуты (строки 58, 74, 90) — оставить как есть (`$hermes`), они автоматически пойдут на v2.

**Коммит:**
```bash
git add AIM/deploy/nginx/iamaim.conf
git commit -m "feat(nginx): blue-green switch chat→hermes-v2, telegram stays on v1"
```

### Шаг 4. Деплой v2 на сервер (blue-green, v1 НЕ трогаем)

```bash
# 1. Push
git push origin feat/competitor-v2-perplexity-searxng  # или main после merge

# 2. На сервере — обновить код
ssh aim "cd /opt/aim/AIM && git fetch && git checkout <branch> && git pull"

# 3. СОЗДАТЬ BACKUP nginx конфига (для отката!)
ssh aim "cp /opt/aim/AIM/deploy/nginx/iamaim.conf /opt/aim/AIM/deploy/nginx/iamaim.conf.pre-v2-switch-$(date +%Y%m%d)"

# 4. Собрать образ v2
ssh aim "cd /opt/aim/AIM && docker compose build hermes-v2"

# 5. Запустить v2 РЯДОМ с v1 (не трогая v1!)
ssh aim "cd /opt/aim/AIM && docker compose up -d hermes-v2"

# 6. Подождать healthcheck (30 сек)
sleep 35

# 7. Проверить health v2 напрямую
ssh aim "docker exec aim-hermes-v2 curl -s http://localhost:8000/health"
# Ожидается: {"status":"ok","service":"hermes-v2","version":"0.3.0"}

# 8. Smoke-тест v2 БЕЗ переключения nginx (через docker exec)
ssh aim "docker exec aim-nginx curl -s http://hermes-v2:8000/health"
# Если ОК — v2 жив и доступен из nginx-сети
```

**Стоп-точка:** если v2 не поднимается или health не отвечает — НЕ переключать nginx. Разбираться.

### Шаг 5. Переключение nginx (1 строка + reload)

Только после успешного Шага 4:

```bash
# nginx читает конфиг из volume mount: ./deploy/nginx/iamaim.conf
# После git pull конфиг уже обновлён на сервере. Нужно только reload:
ssh aim "docker exec aim-nginx nginx -t"     # проверить синтаксис
ssh aim "docker exec aim-nginx nginx -s reload"  # применить
```

### Шаг 6. Smoke-тест в проде (15 мин)

- Открыть iamaim.ru (или тестовую страницу с чатом)
- Написать URL клиники в чат
- Проверить: появляются ли секции 01-04, таблицы, отзывы
- Проверить Telegram бот — должен работать (он на v1)
- Смотреть логи: `ssh aim "docker logs aim-hermes-v2 --tail 50 -f"`

---

## 🔄 Откатная стратегия (мгновенно, <1 минуты)

Если что-то сломалось:

```bash
# Вариант A — вернуть конфиг из backup (Шаг 4.3):
ssh aim "cp /opt/aim/AIM/deploy/nginx/iamaim.conf.pre-v2-switch-* /opt/aim/AIM/deploy/nginx/iamaim.conf"
ssh aim "docker exec aim-nginx nginx -s reload"
# → трафик снова идёт на v1, v2 можно остановить или оставить для дебага

# Вариант B — git rollback:
ssh aim "cd /opt/aim/AIM && git checkout known-good-17jul-0104 -- AIM/deploy/nginx/iamaim.conf"
ssh aim "docker exec aim-nginx nginx -s reload"
```

v1 всё это время работал и продолжит работать — данные не теряются.

---

## ⚠️ Известные риски и ограничения

### Что сломается или ухудшится при переключении:
1. **HTML-отчёт на iamaim.ru/{slug} НЕ будет генерироваться из v2-чатов.** v2 не имеет HTML builder + WP publish. Если бизнес завязан на отчёт-URL — это проблема (нужен Шаг «фаза 2» ниже).
2. **Сессии начнутся с нуля.** v1 хранил в PostgreSQL, v2 — в SQLite `/opt/hermes-v2-data/sessions.db`. Активные диалоги не перенесутся.
3. **Нет аутентификации на v2.** Bearer token из nginx игнорируется. Смягчение: порт 8000 только `expose` (внутри docker-сети).
4. **Разный LLM.** v1: deepseek-v4-pro. v2: glm-5.2. Качество может отличаться.
5. **`/api/chat/send` (location строка 58) получит 404 от v2** — у v2 только `/api/chat/stream`. Проверить, использует ли его фронт.

### Что НЕ сломается:
- Telegram бот (на v1)
- Существующие опубликованные отчёты на iamaim.ru (статичные страницы в WP)
- v1 контейнер — продолжит работать, можно откатиться за 1 минуту

---

## 🔮 Фазы дальнейшего развития (после стабилизации чата на v2)

Если после blue-green захотите полной замены v1 — это отдельные фазы:

- **Фаза 2 (1-2 дня):** Аутентификация — скопировать `hermes/app/auth.py` в v2, добавить `Depends(verify_token)`.
- **Фаза 3 (3-5 дней):** HTML builder + WP publish — перенести `build_report.py` (1500 строк) + `publish_scout_report.py`. Самая большая работа.
- **Фаза 4 (2-3 дня):** Telegram gateway — перенести `telegram_gateway.py` (500 строк) + voice_transcriber.
- **Фаза 5 (1-2 дня):** Mode system (PRESALE/ACTIVE/ADMIN) — упрощённая версия mode_gate.
- **Фаза 6 (по мере надобности):** Дополнительные analysis tools из v1 (run_hh_analysis, run_doctor_dossiers, run_smi_mentions и т.д.)

После Фазы 3-4 можно остановить v1 контейнер полностью.

---

## 📋 Что нужно от вас для старта

1. Подтвердить стратегию blue-green (или сказать «хочу полную замену»).
2. Дать SSH-доступ к серверу `aim` (или подтвердить что могу подключаться).
3. Сказать, на какую ветку деплоить (`feat/competitor-v2-perplexity-searxng` или merge в `main`).
4. Подтвердить, что HTML-отчёты iamaim.ru/{slug} можно пока оставить генерироваться через v1 (или сказать что критично — тогда нужна Фаза 3 в этом плане).