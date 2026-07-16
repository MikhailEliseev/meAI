# Quick Start: После одобрения HH API

## Когда заявка #21272 будет одобрена

### Шаг 1: Получить credentials

1. Зайди на https://dev.hh.ru/admin
2. Найди своё приложение "AIM CI Agent"
3. Скопируй:
   - **Client ID** (например: `ABC123DEF456`)
   - **Client Secret** (например: `xyz789abc123def456`)

### Шаг 2: Получить токен

Запусти скрипт:

```bash
cd AIM
./scripts/get_hh_token.sh YOUR_CLIENT_ID YOUR_CLIENT_SECRET
```

Скрипт автоматически:
- Запросит токен у HH API
- Создаст файл `.env` с токеном
- Покажет токен в консоли

### Шаг 3: Проверить токен

```bash
# Проверка через curl
source .env
curl -H "Authorization: Bearer $HH_ACCESS_TOKEN" \
     -H "HH-User-Agent: AIM-CI-Agent/1.0 (me@mikhaileliseev.com)" \
     "https://api.hh.ru/vacancies?employer_id=1740&per_page=1"
```

Если видишь JSON с вакансиями — всё работает! 🎉

### Шаг 4: Запустить HH Agent

```bash
cd AIM
source ../venv/bin/activate
PYTHONPATH=src:../src python scripts/test_hh_agent.py
```

Агент:
- Соберёт вакансии Яндекса, Сбера, VK
- Сохранит снимки в `obsidian/ci-hh/raw/snapshots/`
- Создаст отчёт в `obsidian/ci-hh/wiki/insights/`

### Шаг 5: Проверить результаты

```bash
# Посмотреть снимки
ls -la obsidian/ci-hh/raw/snapshots/$(date +%Y-%m-%d)/

# Посмотреть отчёт
cat obsidian/ci-hh/wiki/insights/report-$(date +%Y-%m-%d).md
```

---

## Если что-то пошло не так

### Ошибка 403 Forbidden

- Проверь, что токен в `.env` правильный
- Проверь, что заявка одобрена на https://dev.hh.ru/admin

### Ошибка "No module named 'aim'"

```bash
# Убедись, что PYTHONPATH установлен
cd AIM
PYTHONPATH=src:../src python scripts/test_hh_agent.py
```

### Токен не работает

Запроси новый токен:

```bash
./scripts/get_hh_token.sh YOUR_CLIENT_ID YOUR_CLIENT_SECRET
```

**Важно:** При повторном запросе старый токен отзывается!

---

## Что дальше

После успешного запуска:

1. ✅ HH Agent работает
2. ⏳ Настроить расписание (ежедневный мониторинг)
3. ⏳ Добавить больше конкурентов
4. ⏳ Создать CI Magister (координатор)
5. ⏳ Добавить другие микроагенты (Web, Social, News)
6. ⏳ Интегрировать с Operator

---

**Создано:** 2026-05-04T22:36:00+03:00  
**Статус заявки:** #21272, рассматривается
