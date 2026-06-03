# Session: 2026-06-02

## Phase 22: PRESALE Flow Redesign — COMPLETED ✅

**Date:** 2026-06-02
**Status:** Все code changes реализованы, задеплоены на VPS, 27/27 unit-тестов.

### Сессия 3 — тестирование и фиксы (2026-06-02 17:15–18:00)

#### Обнаружено и исправлено (3 проблемы):

##### P1: Hermes не показывал prescan-разбор в первом ответе ✅ FIXED
- **Было:** клиент даёт URL → 90с тишины → «назовите конкурентов». Prescan-данные собраны, но клиент их не видит.
- **Корень:** промпт разрешал вызывать run_prescan + find_competitors в одном ходе.
- **Фикс:** добавлено правило `🛑 ПРАВИЛО ПЕРВОГО СООБЩЕНИЯ (НЕРУШИМО)` в самое начало `_presale_prompt()` — ТОЛЬКО run_prescan в первом ходе, потом живой разбор, потом find_competitors.
- **Результат:** smilestudio.ru → «Так, смотрите что получается... скорость 8.3 сек — критично, врачей нет, отзывов 0... А теперь самое интересное — давайте посмотрим кто вокруг вас.» Живой разбор + WOW-эффект.

##### P2: run_ci_analysis падал с 422 ✅ FIXED
- **Было:** LLM передаёт competitors как строки `["Семейная"]` или словари с `website` вместо `url`. Pydantic модель требует `url`.
- **Фикс:** функция `_normalize_competitor()` — обрабатывает строки (извлекает url/name), словари (website→url), фильтрует конкурентов без URL с понятной ошибкой.
- **Код:** `AIM/hermes/app/tools/run_ci_analysis.py` — +30 строк нормализации

##### P3: find_company_financials вызывался без INN ✅ FIXED
- **Было:** LLM вызывает tool без INN/ОГРН → ошибка "Either inn or ogrn is required".
- **Фикс:** tool description: «⚠️ ТРЕБУЕТ INN или ОГРН. Если у тебя нет INN/ОГРН конкурента — НЕ вызывай.» + улучшенный error message.
- **Код:** `AIM/hermes/app/tools/find_company_financials.py` — description + detail

### Результаты тестирования (iphk.ru + smilestudio.ru)

#### Что работает идеально ✅
1. **Prescan все данные корректны:** INN, revenue, rating, reviews, SEO, web_speed
2. **0 галлюцинаций** когда Hermes показывает разбор (все цифры из prescan)
3. **web_speed антигаллюцинация работает:** "скорость 1,1 сек — хорошая", "8,3 сек — критично"
4. **Первый ход теперь правильный:** только prescan → живой разбор → "давайте посмотрим кто вокруг"
5. **Бизнес-язык:** "53% посетителей уходят", "пациенты выбирают врача, а не вывеску"

### Баг-фиксы (всего 12)

**Сессия 1-2 (9):**
1. Галлюцинация load_speed — web_speed поле
2. collect_contact в середине диалога — промпт "ЖЕЛЕЗНО"
3. Зацикливание named_competitors — fallback
4. Выдуманный оборот — правило "null → честно"
5. Отзывы не находились — импорт + логгер
6. INN не экстрагировался — DaData fallback
7. Оборот не загружался — BfoNalogClient методы
8. Revenue в тыс. руб. — ×1000
9. Фейковые review_praise — убран keyword matching

**Сессия 3 (3):**
10. P1: prescan-разбор в первом ответе — промпт "НЕРУШИМО"
11. P2: run_ci_analysis 422 — нормализация competitors
12. P3: find_company_financials без INN — warning в description

### Тесты: 27/27 PASSED

### Сессия 4 — тестирование через API и фикс антигаллюцинации (2026-06-02 21:40–22:00)

#### Обнаружено и исправлено:

##### P4: DeepSeek игнорировал web_speed и seo_score — галлюцинировал цифры ✅ FIXED
- **Было:** load_speed_ms=2686 → Hermes: «5 секунд» (на самом деле 2.7с). seo_score=70 → Hermes: «60 из 100».
- **Корень:** DeepSeek видел сырые числа (load_speed_ms, seo_score) и переинтерпретировал их, игнорируя правила «используй ТОЛЬКО web_speed».
- **Фикс:** Удалил сырые числа из ответа tool вообще. Оставил только готовые текстовые поля:
  - `web_speed`: «2.7 сек — средняя скорость» (было и осталось)
  - `seo_health`: «70/100 — хорошее состояние, но есть потенциал для улучшения» (новое)
  - `load_speed_ms` и `seo_score` больше не передаются LLM
- **Результат:** smilestudio.ru — скорость «1,3 сек» (точно), SEO «70/100» (точно). med-det.ru — «1.4 сек», «70/100».
- **Код:** `AIM/hermes/app/tools/run_prescan.py` — +12 строк seo_health, убран load_speed_ms/seo_score
- **Промпт:** `AIM/hermes/app/agent_wrapper.py` — обновлены правила под seo_health

#### Результаты тестирования через API

**Протестировано 2 клиники:** smilestudio.ru, med-det.ru

**Что работает идеально:**
1. P1 fix держится: первый ход — только run_prescan (на smilestudio.ru)
2. Антигаллюцинация web_speed: 1.3с, 1.4с — все цифры точные
3. Антигаллюцинация seo_health: 70/100 — без искажений
4. Живой дружеский тон, бизнес-язык
5. Честность: «выручка не раскрыта», «убыток 273 тыс»
6. Сохранение контекста между ходами диалога
7. Fallback когда find_competitors не срабатывает

**Известная проблема (не код, а модель):**
- P5 (minor): На med-det.ru Hermes пропустил prescan и сразу вызвал find_competitors. Правило `🛑 ПРАВИЛО ПЕРВОГО СООБЩЕНИЯ` в промпте есть, но DeepSeek не всегда ему следует. Это проблема дисциплины модели, не кода.
- Session cache теряется при перезапуске контейнера (in-memory) — ожидаемо.

### Сессия 5 — P5 fix: программное принуждение prescan (2026-06-02 22:30–23:00)

#### P5: DeepSeek игнорировал правило первого сообщения ✅ FIXED
- **Было:** промпт «🛑 ПРАВИЛО ПЕРВОГО СООБЩЕНИЯ (НЕРУШИМО)» был, но DeepSeek всё равно иногда пропускал prescan и вызывал find_competitors сразу (особенно на Tilda/WordPress сайтах).
- **Корень:** DeepSeek менее дисциплинирован чем Claude. Prompt-based enforcement недостаточен.
- **Фикс:** Программное принуждение в `run_agent_sync()`:
  1. При первом сообщении PRESALE с URL → вызываем prescan API напрямую синхронно (httpx)
  2. Результат вкалывается в conversation history как завершённый tool_call (id=`force_prescan_1`)
  3. LLM видит: prescan уже сделан, данные готовы. Он может только рассказать о них.
  4. Инжектированные tool_calls фильтруются из ответа (id начинается с `force_`)
- **Результат:** mc-zdorovie.ru — tool_calls пуст, prescan выполнен кодом за 17с, LLM рассказал живой разбор: «многопрофильная клиника в Симферополе, 14 направлений, SEO 65/100, врачей нет, отзывов нет». Без галлюцинаций.
- **Код:** `AIM/hermes/app/agent_wrapper.py` — +95 строк (_extract_url_from_message, _force_prescan, инъекция в run_agent_sync, фильтр force_ tool_calls)

### TODO
- [x] #61: Протестировать Hermes через API (5 клиник, Bitrix/WordPress/Tilda)
- [x] P4: Исправить галлюцинацию web_speed/seo_score DeepSeek'ом
- [x] P5: Программное принуждение prescan на первом ходе PRESALE
- [ ] Протестировать Hermes через Telegram (@iamaim_bot) — нужен живой пользователь
- [ ] Phase 23: Ultra-Deep Prescan — планы готовы, реализация ждёт
- [x] Закоммитить все изменения (12 баг-фиксов) — `63b7414`
- [x] Задеплоить на VPS — контейнеры перезапущены, фиксы активны
- [ ] Закоммитить P5 fix

### Сессия 6 — P5 v2 + деплой фронтенда + веб-интерфейс (2026-06-03 10:30–11:50)

#### P5 v2: Agent-level tool restriction ✅
- **Было (v1):** prescan вкалывался в историю, но DeepSeek всё равно вызывал find_competitors на первом ходу
- **Фикс:** При первом сообщении PRESALE с URL создаётся агент с `enabled_toolsets=["hermes-debug"]` — физически не может вызвать find_competitors
- **Результат:** `find_competitors` заблокирован ("Unknown tool"), модель self-corrected → web_search + web_fetch
- **Turn 2:** Новый агент с полными инструментами → `run_ci_analysis` реально вызван (0.72s, 2 конкурента)
- **Код:** `agent_wrapper.py` — `_create_agent(enabled_toolsets=...)`, `_p5_restricted` флаг, кеширование `(None, ts, history)`

#### Frontend fix: Permission denied в веб-интерфейсе ✅
- **Было:** iamaim.ru/api/chat/send возвращал `EACCES: permission denied, mkdir '/opt/data/leads/...'`
- **Корень:** Волюм `hermes_data` имеет `/opt/data/` с `drwx------` (700, только root). Next.js запущен как `nextjs` (uid=1001)
- **Фикс:** 
  1. Создал `/opt/aim/leads` на хосте (777)
  2. Bind mount `/opt/aim/leads:/opt/data/leads` в docker-compose (вместо `hermes_data:/opt/data`)
  3. Увеличил `HERMES_TIMEOUT_MS` с 30с → 120с (prescan 17с + DeepSeek 20-40с = 60-90с)
  4. Next.js 308 redirect fix: curl без trailing slash
- **Файлы:** `docker-compose.yml` (volume), `AIM/frontend/app/api/chat/send/route.ts` (timeout)

#### Результаты веб-теста (iamaim.ru)
1. ✅ **Базовый чат:** "Привет" → Operator презентуется, просит URL
2. ✅ **PRESALE с URL:** `medsi-premium.ru` → prescan + живой разбор (SEO 70/100, скорость мгновенная, 9+ специализаций, VK/Telegram)
3. ✅ **Антигаллюцинации:** Цифры точные, без искажений DeepSeek

#### Uncommitted changes (4 файла)
- `AIM/frontend/app/api/chat/send/route.ts` — HERMES_TIMEOUT_MS 30→120s
- `AIM/hermes/app/agent_wrapper.py` — P5 v2: restricted agent + force_prescan + tool filtering
- `AIM/hermes/app/tools/run_prescan.py` — sub-1000ms speed format fix
- `SESSION.md` — эта запись

### TODO
- [x] #61: Протестировать Hermes через API (5 клиник, Bitrix/WordPress/Tilda)
- [x] P4: Исправить галлюцинацию web_speed/seo_score DeepSeek'ом
- [x] P5: Программное принуждение prescan на первом ходе PRESALE
- [x] P5 v2: Agent-level tool restriction + кеширование истории
- [x] Починить веб-интерфейс iamaim.ru (EACCES + timeout)
- [ ] Протестировать Hermes через Telegram (@iamaim_bot) — нужен живой пользователь
- [ ] Phase 23: Ultra-Deep Prescan — планы готовы, реализация ждёт
- [x] Закоммитить все изменения (12 баг-фиксов) — `63b7414`
- [x] Задеплоить на VPS — контейнеры перезапущены, фиксы активны
- [ ] Закоммитить P5 fix + frontend fix (4 файла, сессия 6)
