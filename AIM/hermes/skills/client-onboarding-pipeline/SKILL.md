---
name: client-onboarding-pipeline
version: 5.5.0
description: >-
  Единый протокол онбординга клиента в чате: 15 фаз Pre-flight--Presentation.
  v5.5: Integration Code — 5 примеров кода (Profile/Post/YouTube/Telegram/Google Maps) + общий шаблон вызова с polling.
  v5.4: Iron Rule #11 — Tool Self-Repair (3 прохода диагностики).
  v5.3: Apify Actor Registry — 6 верифицированных акторов.
  v5.2: Instagram fallback ladder + VC.ru Bayes + robots.txt AI-crawler check.
  v5.1: Competitor Doctor 3-Pass Social Verification (Phase 4, Step 8.1-A/B/C).
  Корень: уроки Детства Плюс (верификация соцсетей + системный поиск
  конкурентов) и ARclinic (Pre-flight Hard Gate).
  конкурентов) и ARclinic (Pre-flight Hard Gate).
rating: 5
triggers:
  - Клиент в чате (добавлен в группу или написал первым)
  - Команда /onboard выполнена
  - Новая сессия, первое сообщение клиенту
  - Запрос "покажи что умеешь" от клиента
  - Дрифт темы: после дизайна/стилистики/экспериментов → клиент в чате
  - Сообщение «добавил тебя в чат» / «начинай с [клиент]»
---


---

---

## 🔴🔴🔴 ПРОЧИТАЙ ЭТО ПЕРВЫМ — EXECUTION WARNING 🔴🔴🔴

**Ты уже трижды провалил онбординг (Детство Плюс, ARclinic, VIP Clinic) потому что ЗАГРУЖАЛ скилл, но НЕ ВЫПОЛНЯЛ его.**

Этот скилл — не справочник. Это чек-лист. Каждая фаза содержит Execution Log с [ ] галочками.

**Жёсткое правило:** если ты прочитал фазу и не запустил инструмент из её Execution Log — ты имитируешь работу. Пустой [ ] = фаза не завершена. Не переходи дальше.

**Онбординг может длиться час. Это нормально.** Не прерывайся, не спрашивай «продолжить?», не пытайся ускориться ценой качества. Пиши статусы как есть: «Phase 4 занял 18 минут — собрано 12 конкурентов из 3 источников». Документ, который ты создаёшь — это не отчёт. Это фундамент для всего дальнейшего проекта. Каждая цифра, каждый конкурент, каждая боль пациента — пойдут в стратегию, контент-план, рекламные кампании. Если сэкономишь час сейчас — потратишь недели потом на исправление.

Ты НЕ имеешь права:
- Заменять Яндекс.Карты на web_search
- Пропускать cross-employment врачей
- Писать «конкуренты примерно такие»
- Генерировать контент-план без слоёв (форумы + конкуренты + тренды)
- Переходить к HTML с незаполненным Execution Log

**Перед каждым переходом к следующей фазе — self-check: «Все ли [ ] → [x]? Если нет — возвращаюсь и запускаю.»**

---

## Навигация (карта скилла)

| Секция | Что |
|--------|-----|
| Железные правила (0-10) | Обязательные правила, без исключений |
| Tool Failover Protocol | Ротация ключей Apify/Firecrawl |
| Фаза->Инструмент->Модель | Таблица маршрутизации |
| Фаза 0: PRE-FLIGHT | Авто-загрузка скиллов при входе |
| Фаза 0.5: Deep Research | Автономное исследование |
| Фаза 0.75: Audience Analysis | Patient Persona |
| Фаза 1: Tech Audit | SEO, Speed, GEO, Schema |
| Фаза 2: Social Verifier | IG/TG/VK/YouTube/Дзен |
| Фаза 3: Content Analysis | Контент врачей, форматы, ER |
| Фаза 3.5: Key Persons + SMI | 4-tier врачей, 3 поиска СМИ |
| Фаза 3.6: SMI Placement Map | Каналы размещения, бюджеты |
| Фаза 4: Competitors | ProDoctorov, scorer, deep анализ |
| Фаза 5: Forum Pains + Reviews | Форумы, отзывы, тональность |
| Фаза 6: Finance | Выписка ФНС, Rusprofile |
| Фаза 7: Content Plan | Супер-темы (3 слоя + TOFU/MOFU/BOFU) |
| Фаза 8: HTML Build | Генерация КП (12/11 блоков) |
| Фаза 9: QC Critique | 3 прохода, 10 проверок |
| Фаза 10: Presentation | Отправка + summary |
| Post-Mortems | Уроки из реальных кейсов |
| Implementation Notes | Детали реализации правил |

**Реестр зависимостей:** `references/dependencies.md`
**Чейнджлог:** `references/CHANGELOG.md`
**Instagram fallback:** `references/instagram-fallback-ladder.md`
**Режим:** presale (12 блоков) / onboarding (11 блоков, без CTA)

---


## ⚠️ ДОЛЖЕН БЫТЬ ПЕРВЫМ СКИЛЛОМ ПРИ ВХОДЕ В ЧАТ С КЛИЕНТОМ

**Ты загружаешь этот скилл ПЕРВЫМ ДЕЛОМ, когда появляется клиент.**

Вот сигналы что пора загрузить:
- Тебя добавили в чат с незнакомыми людьми
- Пользователь сказал «познакомься с [клиент]», «начинай», «добавил тебя»
- Контекст переключился: только что обсуждали дизайн/эксперименты → пришёл клиент
- Ты не уверен, загружал ли этот скилл в этой сессии

**Если хоть один сигнал есть — СТОП. Загрузи скилл сейчас. Выполни PRE-FLIGHT Phase 0. Только потом пиши клиенту.**

**Почему (ARclinic, июнь 2026):** Обсуждали дизайн-систему → контекст ушёл от уроков Детства Плюс → добавили в чат с клиентом → начал без перезагрузки → повторил ошибки. Контекст перегружен, а скилл не перезагружен — рецепт провала.

# Онбординг-пайплайн: Клиент в чате

## Железные правила (железобетонные, без исключений)

### 0. RESULT GATE — 2 цикла проверки прежде чем показать результат (ЖЁСТКО)

**Корень проблемы (ARclinic, июнь 2026):** я прошёл 8 из 15 фаз, сделал HTML и сказал «готово». 7 фаз были недоделаны. Пользователь в ярости. Это недопустимо.

**Жёсткое правило:** когда ты готов показать результат — ты НЕ готов. Сначала — 2 полных цикла проверки.

#### Цикл 1 (SELF-CHECK):
1. Открыть этот скилл
2. Пройти по КАЖДОЙ фазе 0→10
3. Проверить Execution Log каждой фазы
4. Каждый пустой `[ ]` — это НЕЗАВЕРШЁННАЯ работа
5. Составить список: какие фазы недоделаны? Какие инструменты не запущены?
6. **НЕ показывать список. Молча вернуться к недоделанным фазам и ДОДЕЛАТЬ.**

#### Цикл 2 (FINAL VERIFY):
1. После доделывания — снова пройти по ВСЕМ фазам
2. Все ли `[ ]` → `[x]`?
3. Все ли инструменты были РЕАЛЬНО запущены (не заменены на web_search)?
4. data.json содержит все 14 секций?
5. Если остались gaps → вернуться и добрать (ещё 1 цикл)
6. **Только когда 2 цикла подряд показали «всё [x]» — показать результат.**

**Сигналы что ты собрался срезать (остановись!):**
- Ты думаешь: «этого достаточно, отдам так»
- Ты написал «готово» или «файл готов»
- Ты хочешь спросить «нормально?» вместо проверки
- Ты считаешь фазы мысленно а не по чек-листу

**Что делать вместо «готово»:**
```
❌ «Готово. Файл здесь.»
✅ «Цикл 1: Phase 0.75 недоделан (audience), Phase 1 нет PageSpeed, Phase 5 нет форумов. 
   Запускаю недостающие инструменты. Цикл 2: все [x], gaps закрыты. Файл здесь.»
```

### 00. FULL AUTO MODE — НИКОГДА НЕ СПРАШИВАТЬ РАЗРЕШЕНИЯ. ДЕЛАТЬ ДО КОНЦА.
Ты работаешь в режиме ПОЛНОГО АВТОМАТА. Никаких исключений.

Ты НИКОГДА не спрашиваешь разрешения:
- ❌ «Продолжить?» — НЕТ. Просто продолжаешь.
- ❌ «Запустить Phase N?» — НЕТ. Запускаешь молча.
- ❌ «Нормально?» / «Туда копаю?» — НЕТ.
- ❌ «Показать промежуточный результат?» — НЕТ.
- ❌ «Нужно ли проверить...?» — НЕТ. Проверяешь сам.
- ❌ «Это уже час длится — может, остановимся?» — НЕТ. Доделываешь до конца.

Ты делаешь ТОЛЬКО:
- ✅ Получил URL → запустил ВСЕ 15 фаз подряд → показал готовый документ
- ✅ Сообщаешь только о КРИТИЧЕСКИХ ошибках (сайт не открылся, все ключи exhausted)
- ✅ Пишешь статусы как есть: «Phase 4 — 18 минут, 12 конкурентов из 3 источников»
- ✅ Всё остальное — молча, автоматом, без пауз

**Онбординг может длиться час. Это нормально.** Сэкономленный час = потерянные недели на исправление потом. Документ — фундамент всего дальнейшего проекта.

### 1. Параллельное выполнение
Когда данных накопилось на несколько фаз — запускай ВСЕ workstreams ПАРАЛЛЕЛЬНО через delegate_task, а не последовательно:
```
delegate_task(tasks=[
  {"goal": "Phase 1: tech-audit сайта (8 параметров)"},
  {"goal": "Phase 4: конкуренты через find-competitors.py + Revenue Gap"},
  {"goal": "Phase 2: верификация IG клиники и всех врачей"},
  {"goal": "Phase 3: контент-анализ Instagram клиники"}
])
```

### 2. PRE-FLIGHT + DRIFT PROTECTION (два триггера — одно правило)

**Триггер А — Новый клиент (PRE-FLIGHT):**

При первом сообщении в любом чате (клиентском или админском):
- МОЛЧА загрузить 5 скиллов (skill_view)
- МОЛЧА проверить скрипты (ls /root/bin/)
- МОЛЧА проверить Apify бюджет
- МОЛЧА проверить data.json (если есть slug)

Все проверки заняли <5 секунд. Их не нужно показывать.
Если ВСЁ ок → сразу первое сообщение клиенту.
Если НЕ ок → ТИХОЕ уведомление в DM админа, работа с клиентом продолжается.

**Триггер Б — Дрифт контекста (DRIFT PROTECTION):**

Сигналы входа в режим клиента (любой из):
1. Сообщение содержит URL сайта клиники
2. «добавил тебя в чат», «начинай с [клиент]», «это [имя], владелец [клиника]»
3. Название клиники + вопрос про услуги/анализ
4. «онбординг», «presale», «сделай КП», «изучи сайт», «сделай аудит»
5. Упоминание @ (добавление в групповой чат)

Маркеры дрифта (если обнаружены → перезагрузить ВСЕ 5 скиллов принудительно):
- Обсуждали визуал/дизайн систему → пришёл клиент
- Делали эксперименты → пришёл клиент
- Настраивали конфиги, скиллы, окружение → пришёл клиент
- Прошло >30 сообщений с момента последней загрузки онбординг-пайплайна
- Последние 5 сообщений НЕ содержат: «клиент», «онбординг», «presale», «КП», «аудит», «врач», «конкурент»

Алгоритм при сигнале:
1. Распознать сигнал (BOUNDARY SWITCH)
2. Проверить маркеры дрифта
3. Если дрифт: skill_view('client-onboarding-pipeline') + проверить Phase 0
4. Клиенту — молча. Никаких сообщений о процессе.

**Подробное описание механизма:** `references/soul-protection-mechanism.md`

**Реальный кейс (ARclinic, июнь 2026):** 3 часа обсуждали дизайн-систему → добавили в чат → начал без перезагрузки скилла → повторение всех ошибок Детства Плюс.

**Жёсткое правило:** «Без загрузки 5 скиллов — ни слова клиенту.» Загрузка происходит АВТОМАТИЧЕСКИ, без участия пользователя. Не ждать — делать.

### 3. Только бот в чате с клиентом (Hard Gate)
**ЗАПРЕЩЕНО:** MTProto/Telethon (Людмила) для чата с клиентом, invite link через сторонний аккаунт, чтение истории не через бота.

**MTProto -- только для разведки:** поиск каналов, врачей, постов. Не чатов с клиентами.

**MTProto Status (09.06.2026): ЖИВОЙ.** Telethon 1.43.2 + python-socks 2.8.1. HTTP-прокси: 193.111.152.14:7451. Аккаунт: Людмила (ID 7761664791). Доступны: поиск каналов, чтение постов, подписчики, просмотры, реакции. Для поиска врачей/каналов — прямой MTProto-запрос через Telethon. В data.json → `sources.telegram_method: "mtproto"`.

**Документация MTProto:** `references/mtproto-join-invite-link.md` — технический шаблон (Telethon + SOCKS5), инцидент ARclinic, правила использования.

### 4. 11 проверок перед отправкой
1. Instagram клиники -- верифицирован? Не из старого скрапа?
2. Instagram конкурентов -- верифицирован? Каждый @username проверен?
3. Контент-анализ врачей -- сделан? Темы/форматы/топ-посты/пробелы?
4. data.json содержит секцию `content_analysis` с темами/форматами/топ-постом каждого ключевого врача?
5. Конкуренты -- найдены системно? ProDoctorov, find-competitors.py?
6. Форумы собраны? Woman.ru / IRecommend / Pikabu с топ-15 болей?
7. СМИ-ссылки — 3 поиска (деловые, глянец, мед) + регионалы? Прямые URL статей, а не названия изданий?
8. Каждая цифра в 2+ источниках (для multi-source данных: подписчики, ER, выручка). Single-source данные (GEO-схемы, llms.txt, SEO-теги) — 1 источник, помечать как «верифицировано: 1 источник».
9. data.json структурирован (14 секций)?
10. Tech audit перепроверен? Speed через 2 источника, GEO-схемы browser_console, verified_at свежий?
11. SMI клиента перепроверено? 3 поиска в этой сессии или <30 мин назад?

### 5. 3 прохода с QC (автомат)
После каждого прохода QC1-QC10 -> исправить. Все 3 подряд, без пауз. Результат -- после 3-го.

### 6. Ничего технического клиенту
Ни путей, ни JSON, ни фаз, ни Apify/Firecrawl, ни exit-кодов. Только человеческий язык.

### 7. Запрещённые термины
- Длинные тире (---) НИГДЕ. Только короткие (-) или дефисы
- "EGRUL" -> "выписка ФНС"
- "мёртвый/трупный" -> "неактивный"
- "научим/починим/ставим" -> "поможем интегрировать"
- Директивный тон -> уважительный партнёрский

### 8. MODEL ROUTING (Hard Gate)
- **Flash (deepseek-v4-flash)**: быстрые действия + генерация HTML по шаблону + контент-план (Phase 7) + HTML Build (Phase 8). Запуск скриптов, технические проверки, HTML-трансформация.
- **Pro (deepseek-v4-pro)**: ВСЁ, что требует глубины — контент-анализ врачей, форумы, SMI, финансы, анализ конкурентов, генерация HTML, написание любых текстов клиенту
- **Flash МОЖЕТ генерировать HTML** — ИСПОЛЬЗУЙ ШАБЛОН templates/client-kp-template.html как основу. Заполни плейсхолдеры данными из data.json. Без самодеятельности в CSS — бери CSS из шаблона as-is.

### 9. GOAL LOOP — возврат к незакрытым gaps

При обнаружении gaps (незакрытых проверок) после Phase 9:
- Вернуться к Phase 2–5 для сбора недостающих данных
- Stopping condition: gaps = 0 ИЛИ 3 полных цикла без новых данных
- Перед HTML: честно указать оставшиеся gaps в секции «Допущения и ограничения»
- Gaps отслеживаются в data.json: поле `data.gaps` — массив строк

Детали реализации: см. Implementation Notes в конце скилла.

### 10. EXECUTION GATE — не читать, а ДЕЛАТЬ (Hard Gate)

**Каждая фаза содержит Execution Log с [ ] чек-листом. Ты ОБЯЗАН:**

1. Перед переходом к следующей фазе — прочитай Execution Log текущей фазы
2. Если любой `[ ]` пуст — **вернись и ЗАПУСТИ инструмент.** Не пиши «надо бы», не переходи дальше.
3. Только когда все `[ ]` → `[x]` — фаза завершена.
4. В конце каждой фазы — короткий self-check: «Фаза N: все ли [x]? Если нет — возвращаюсь.»

**Почему:** Ты трижды (Детство Плюс, ARclinic, VIP Clinic) загружал скилл, читал требования — и НЕ выполнял инструменты. Execution Log физически не даст пропустить: пустой [ ] = незавершённая фаза = СТОП.

**Запрещено:**
- ❌ «Надо бы запустить find-competitors.py» — НЕТ. Запусти.
- ❌ «Яндекс.Карты должны показать похожие» — НЕТ. Открой browser_navigate.
- ❌ «Конкуренты примерно такие» — НЕТ. Без verified источника не записывай.
- ❌ Переход к HTML с незаполненным Execution Log

### 10a. TOOL FALLBACK — при отказе инструмента (Hard Gate)

Если инструмент из [ ] отвалился (402, timeout, blocked, нет ключей):

1. **НЕ пропускать фазу.** НЕ ставить [x] мысленно.
2. Применить Tool Failover Protocol (см. выше): ротация ключей → следующий инструмент → fallback-цепочка.
3. Если ВСЕ fallback'и исчерпаны → записать в data.json `gaps`:
   ```
   "phase_N_tool_failed": "Яндекс.Карты не открылись, MTProto недоступен. Конкуренты найдены через DocDoc (fallback)."
   ```
4. В [ ] написать: `[x] через fallback (DocDoc) — см. gaps`
5. Клиенту в КП — честно: «Данные собраны через доступные источники. Для полного аудита требуется [конкретный инструмент].»

### 10b. TOOL VERIFICATION — правильный ли инструмент? (Hard Gate)

**Самая частая ошибка:** ты читаешь «найди конкурентов» и делаешь `web_search` — потому что это быстрее. Но скилл требует `browser_navigate Яндекс.Карты + cross-employment + DocDoc`.

После КАЖДОГО заполненного [x] — сверься:

```
Что требовал скилл:   browser_navigate → Яндекс.Карты «Похожие места»
Что я сделал:         web_search «конкуренты рядом»
Совпадает?            ❌ НЕТ → переделать правильным инструментом
```

Если инструменты не совпадают — [x] не засчитывается. Переделай.

**Примеры подмен (запрещены):**
- `browser_navigate Яндекс.Карты` → заменять на `web_search` ❌
- `find-competitors.py` → заменять на `web_search prodoctorov` ❌
- `Apify Profile Scraper (RESIDENTIAL)` → заменять на `web_search site:instagram.com` ❌
- `MTProto resolve` → заменять на `web_search site:t.me` ⚠️ (только как fallback с пометкой)
- `EGRUL 2-шаг` → заменять на `web_search выручка` ⚠️ (только как fallback)

### 11. TOOL SELF-REPAIR — 3 прохода прежде чем сказать «не работает» (Hard Gate)

**Корень проблемы (ARclinic, июнь 2026):** Apify вернул 404 на всех 22 ключах. Я сказал «Apify мёртв» и переключился на web_search. Пользователю пришлось САМОМУ дать правильные actor URL. Это недопустимо.

**Жёсткое правило:** когда инструмент отказывает — НЕ сообщать «не работает». Пройти 3 прохода самостоятельной диагностики:

#### ПРОХОД 1: Проверить формат запроса

Не: «Apify не работает».
А: «404 на всех ключах. Проверяю формат actor ID.»

- Actor ID со слешем `/` → заменить на тильду `~`
- `apify/instagram-profile-scraper` → `apify~instagram-profile-scraper`
- Проверить: отличается ли формат URL от задокументированного?
- Проверить: правильный ли HTTP-метод? (POST vs GET?)
- Проверить: правильный ли эндпоинт? (`/acts/{id}/runs` vs `/actor-runs`?)

#### ПРОХОД 2: Проверить сам инструмент

- Apify: `/v2/acts/{actor}?token=` — возвращает ли 200 с метаданными актора?
- Firecrawl: `/v1/health` или простой scrape известного URL
- Browser: открыть google.com — работает ли браузер вообще?
- EGRUL: прямой HTTP вместо browser_navigate

#### ПРОХОД 3: Альтернативный инструмент того же класса

- Apify Instagram Profile Scraper не работает → попробовать Apify Instagram Scraper (другой actor)
- Apify не работает → попробовать `browser_navigate` на Instagram
- Browser не работает → `curl` с прокси
- Firecrawl search не работает → `web_search`

**Только после 3 проходов:** доложить «Инструмент X не работает после 3 проходов диагностики. Пробовал: (1) формат URL, (2) health-check API, (3) альтернативный actor Y. Результат: [конкретная ошибка]. Использую fallback Z.»

**Пример правильного поведения (ARclinic):**
```
❌ «Apify вернул 404 на всех ключах. Переключаюсь на web_search.»
✅ «Apify: 404. Проход 1: меняю / на ~ в actor ID → проверяю. 
   Проход 2: health-check /v2/acts/ → актор существует.
   Проход 3: пробую apify~instagram-scraper вместо profile-scraper.
   Результат: profile-scraper заработал с тильдой. Данные получены.»
```

**Это правило защищает от:** пользователя, который вынужден давать ссылки на инструменты, которые я должен был найти сам.

## Tool Failover Protocol (Hard Gate — ротация при любом сбое)

**Золотое правило:** при ЛЮБОЙ ошибке инструмента (402, 403, 429, timeout, пустой ответ, «exhausted») — НЕ останавливаться. Ротировать ключ/инструмент. Только после исчерпания ВСЕХ fallback'ов — докладывать.

### Firecrawl (13 ключей)

```bash
# Перед ЛЮБЫМ Firecrawl-запросом — получить лучший ключ
FIRE_KEY=$(python3 /root/bin/firecrawl-rotate best 2>&1)

# Если скрипт упал — взять первый живой из банка вручную
# Банк: /root/.hermes/keys/firecrawl_keys.json (13 ключей, авто-ротация)
```

**Алгоритм ротации:**
1. `python3 /root/bin/firecrawl-rotate best` → получает ключ с максимальным остатком кредитов
2. Если скрипт вернул ошибку → `cat /root/.hermes/keys/firecrawl_keys.json | python3 -c "..."` → выбрать первый `active` ключ
3. Если ключ вернул 402 → `firecrawl-rotate best` (помечает exhausted, возвращает следующий)
4. Повторять пока есть active ключи
5. Все ключи exhausted → fallback к другим инструментам

**Fallback-цепочка для Firecrawl:**
- Firecrawl ключ #1 → #2 → ... → #13
- Все exhausted → `browser_navigate` (ручной скрап)
- Browser не работает → `curl` с прокси 193.111.152.14:7451
- Прокси не работает → web_search / web_extract

### Apify (22 ключа)

```bash
# Перед ЛЮБЫМ Apify-запросом — проверить бюджет
python3 /root/.hermes/scripts/apify_actor.py --budget

# При ошибке — скрипт автоматически ротирует ключи
# Банк: /root/.hermes/keys/apify_keys.json (22 ключа)
```

**Алгоритм ротации для Instagram:**
1. Текущий ключ → запуск актора `apify~instagram-profile-scraper` (ТИЛЬДА, не слеш!)
2. Ответ: 201 → OK. 404 → неверный actor ID (использован `/` вместо `~` → заменить на `apify~instagram-profile-scraper`). 402 → нет денег. 403 → лимит.
3. Только RESIDENTIAL proxy для Instagram: `"proxy": {"useApifyProxy": true, "apifyProxyGroups": ["RESIDENTIAL"]}`
4. **Питфолл (ARclinic, июнь 2026):** actor ID `apify/instagram-profile-scraper` (слеш) даёт 404 на всех 22 ключах. Правильный: `apify~instagram-profile-scraper` (тильда). После исправления — account-009 и account-010 заработали, результаты за 10-20 секунд.
5. Все ключи exhausted → сообщить пользователю «нужна дозарядка Apify»

### Универсальный Fallback Ladder

```
Инструмент А (основной)
  ↓ exhausted/blocked
Инструмент A ключ #2 (ротация)
  ↓ все ключи exhausted
Инструмент Б (browser_navigate)
  ↓ заблокирован
Инструмент В (curl + прокси)
  ↓ не работает
Инструмент Г (web_search / web_extract)
  ↓ нет результатов
→ Доложить пользователю: «все инструменты исчерпаны, нужно [конкретное действие]»
```

**Правило для памяти агента:** никогда не говорить «не могу». Всегда говорить «инструмент X заблокирован, пробую Y».

## Apify Actor Registry (v5.3 — 6 акторов)

**ВАЖНО: Actor ID использует ТИЛЬДУ (~), не слеш (/).** `apify~actor-name` — правильно. `apify/actor-name` — 404.

| # | Actor | ID | Фаза | Назначение | Input |
|---|-------|----|------|-----------|-------|
| 1 | Instagram Profile Scraper | `apify~instagram-profile-scraper` | Phase 2 | Профили: подписчики, посты, bio, URL | `{"usernames":["..."],"resultsLimit":15,"proxy":{"useApifyProxy":true,"apifyProxyGroups":["RESIDENTIAL"]}}` |
| 2 | Instagram Post Scraper | `apify~instagram-post-scraper` | Phase 3 | Посты: caption, лайки, комментарии, хештеги, @упоминания | `{"username":["..."],"resultsLimit":10}` |
| 3 | Instagram Scraper | `apify~instagram-scraper` | Phase 2-3 | Хештеги, локации, посты, комментарии (универсальный) | `{"searchType":"hashtag","search":"...","resultsLimit":20}` |
| 4 | YouTube Scraper | `streamers~youtube-scraper` | Phase 2 | YouTube: каналы, видео, просмотры, лайки | `{"searchKeywords":"...","maxResults":5}` |
| 5 | Telegram Scraper | `tri_angle~telegram-scraper` | Phase 2 | Telegram: сообщения, подписчики, просмотры (замена MTProto) | `{"profiles":["channel_name_without_@"],"maxMessages":20}` ⚠️ Питфолл (ARclinic 08.06.2026): поле `profiles` (не `channel`), без `@`. Actor запускается (201 OK), но может вернуть пустой `[]` — Telegram-каналы не всегда доступны для скрапинга. Если результат пуст → использовать `web_search site:t.me` как fallback. |
| 6 | Google Maps Scraper | `compass~crawler-google-places` | Phase 4 | Google Maps: конкуренты, рейтинг, отзывы, контакты | `{"searchString":"...","maxPlaces":10,"language":"ru"}` |

**Ротация ключей:** каждый актор → новый ключ Apify (account-008...account-022). При 402/403 → следующий ключ.

**Приоритет использования:**
1. **Profile Scraper** (#1) — всегда первый для верификации Instagram
2. **Post Scraper** (#2) — контент-анализ врачей (caption, engagement, @упоминания)
3. **YouTube Scraper** (#4) — каналы клиники и конкурентов
4. **Telegram Scraper** (#5) — метрики TG-каналов (замена MTProto, который остановлен)
5. **Google Maps** (#6) — дополнительный источник конкурентов (supplement к Яндекс.Картам)
6. **Instagram Scraper** (#3) — поиск по хештегам/локациям (когда нужно найти несвязанные профили)

### Integration Code (5 examples)

**Общий шаблон вызова:**
```python
import requests, json, time

with open('/root/.hermes/keys/apify_keys.json') as f:
    keys_list = list(json.load(f).values())[0]

# account-008..022: ротировать при 402/403
token = keys_list[N]['token']  # N = 7..21 (account-008..022)

r = requests.post(
    f'https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={token}',
    json={PAYLOAD},
    timeout=10
)
run_id = r.json()['data']['id']

# Poll
for _ in range(12):
    time.sleep(8)
    cr = requests.get(f'https://api.apify.com/v2/actor-runs/{run_id}?token={token}', timeout=10)
    if cr.json()['data']['status'] == 'SUCCEEDED':
        break

# Get dataset
dr = requests.get(f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={token}', timeout=10)
items = dr.json()
```

**Пример 1: Instagram Profile Scraper (Phase 2)**
```python
ACTOR_ID = 'apify~instagram-profile-scraper'
PAYLOAD = {
    "usernames": ["arclinic", "reznik_anna_v"],
    "resultsLimit": 15,
    "proxy": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]}
}
# Ответ: [{followersCount, postsCount, biography, fullName, ...}, ...]
```

**Пример 2: Instagram Post Scraper (Phase 3)**
```python
ACTOR_ID = 'apify~instagram-post-scraper'
PAYLOAD = {
    "username": ["arclinic"],
    "resultsLimit": 10
}
# Ответ: [{caption, likesCount, commentsCount, hashtags, mentions, timestamp, ...}, ...]
# ИСПОЛЬЗОВАТЬ ДЛЯ: извлечение тем контента, форматов, ER, @упоминаний врачей
```

**Пример 3: YouTube Scraper (Phase 2)**
```python
ACTOR_ID = 'streamers~youtube-scraper'
PAYLOAD = {
    "searchKeywords": "ARclinic Анна Резник",
    "maxResults": 5
}
# Ответ: [{channelName, subscriberCount, videoCount, viewCount, ...}, ...]
# АЛЬТЕРНАТИВНО: "channelUrl" для прямого скрапа канала
```

**Пример 4: Telegram Scraper (Phase 2 — замена MTProto)**
```python
ACTOR_ID = 'tri_angle~telegram-scraper'
PAYLOAD = {
    "profiles": ["arclinic1"],  # без @, поле называется profiles (не channel!)
    "maxMessages": 20
}
# Ответ: [{message, views, date, ...}, ...] или [] если канал недоступен
# ИСПОЛЬЗОВАТЬ ДЛЯ: подписчики канала, просмотры, активность, упомянутые врачи
# ⚠️ Если результат пуст → fallback: web_search site:t.me "@канал"
```

**Пример 5: Google Maps Scraper (Phase 4)**
```python
ACTOR_ID = 'compass~crawler-google-places'
PAYLOAD = {
    "searchString": "косметология anti-age Санкт-Петербург Верейская",
    "maxPlaces": 10,
    "language": "ru"
}
# Ответ: [{title, address, rating, reviewsCount, phone, website, ...}, ...]
# ИСПОЛЬЗОВАТЬ ДЛЯ: поиск конкурентов рядом, рейтинг, контакты
```

## Карта: Фаза → Инструмент → Модель

| Фаза | Что | Инструмент | Модель |
|------|-----|-----------|--------|
| **0 PRE-FLIGHT** | Загрузить 5 скиллов | `skill_view()` × 5 | — |
| | Проверить скрипты (6 шт) | `ls /root/bin/` | — |
| | Проверить Apify бюджет | `apify_actor.py --budget` | — |
| | Проверить Firecrawl ключ | `firecrawl-rotate best` | — |
| | Проверить MTProto статус | `tg-mtproto.py` ping | — |
| | Проверить disk space | `df -h` | — |
| | Создать директорию проекта | `mkdir -p` | — |
| | Проверить browser | `browser_navigate` google.com | — |
| | Уведомить админа (если FAIL) | `send_message()` DM | — |
| **0.5 Deep Research** | Извлечь врачей с сайта | `browser_navigate` + `browser_console` (Bitrix) / `web_extract` | **Pro** |
| | Deep research врача | Firecrawl Deep Research / `delegate_task` | **Pro** |
| | Исследование клиники | `web_search` + `web_extract` | **Pro** |
| | Классификация врачей | анализ → data.json | **Pro** |
| **0.75 Audience** | Демография, источники трафика | Яндекс.Метрика / GA / форумы | **Pro** |
| | Пациентские сегменты (LTV, repeat rate) | синтез из форумов + отзывов | **Pro** |
| **1 Tech Audit** | Speed, broken links, meta, H1, alt, sitemap, SSL, mobile | `curl` + `browser_console` | **Flash** |
| | Speed + GEO топ-5 конкурентов | PageSpeed API + browser_console | **Flash** |
| | Сравнительная таблица клиент vs конкуренты | запись в data.json | **Pro** |
| **2 Social Verifier** | verify-social-accounts.py | `terminal()` | **Flash** |
| | Apify Profile Scraper batch | `apify_actor.py` → `apify~instagram-profile-scraper` | **Flash** |
| | Apify YouTube Scraper | `apify_actor.py` → `streamers~youtube-scraper` | **Flash** |
| | Apify Telegram Scraper | `apify_actor.py` → `tri_angle~telegram-scraper` | **Flash** |
| | Google site:search | `web_search` | **Flash** |
| | Broad search (VK/TG/YouTube) | `web_search` + `browser_navigate` | **Flash** |
| | Cross-contamination | `browser_navigate` | **Flash** |
| | Мастер-таблица врачей | сводка в data.json | **Pro** |
| **3 Content Analysis** | Apify Post Scraper (caption, лайки, @mentions) | `apify_actor.py` → `apify~instagram-post-scraper` | **Flash** |
| | Анализ тем/формата/фишки/топ-поста | анализ | **Pro** |
| | ER engagement rate | расчёт | **Flash** |
| | Тренд ER | расчёт | **Flash** |
| | Формат-победитель | анализ | **Pro** |
| | Founder Brand Gap Diagnosis | анализ | **Pro** |
| | Запись content_analysis | `write_file()` | **Pro** |
| **3.5 Key Persons+SMI+Vacancy** | 4-tier классификация | анализ | **Pro** |
| | SMI поиск (4 поиска (деловые+массовые, глянец, мед, регион)) | 3× `web_search` site: | **Pro** |
| | **Расширенный SMI-поиск без site:** | `web_search` широкий | **Pro** |
| | Извлечение URL статей | `web_extract` | **Pro** |
| | Vacancy: сайт клиники | `web_extract` | **Flash** |
| | Vacancy: hh.ru employer | `browser_navigate` + `browser_console` | **Flash** |
| | Vacancy: конкуренты | `browser_navigate` + `browser_console` | **Flash** |
| | Анализ вакансий | синтез → data.json | **Pro** |
| **3.6 SMI Placement** | SMI как канал размещения | smi_media_map.md + синтез | **Pro** |
| | Gap-анализ размещений конкурентов | сравнение с топ-3 | **Pro** |
| **4 Competitors** | ProDoctorov Auto-Discovery | `find-competitors.py` | **Flash** |
| | Proximity Sweep | web_search site:yandex.ru/maps | **Flash** |
| | Выписка ФНС топ-5 | прямой HTTP (terminal: curl) | **Flash** |
| | Revenue Gap + Large Group | расчёт | **Flash** |
| | Competitor Clustering + Scorer | анализ 5 кластеров | **Pro** |
| | **Competitor Doctor 3-Pass Social Verify** (8.1-A/B/C: сайт+Apify→broad+VK/TG→cross-contam) | Apify + web_search + browser_navigate | **Pro** |
| | **Deep Content Analysis топ-3** (ключевые врачи, IG скрап, темы/ER/пробел, SMI, WOW-инсайты) | Apify + web_search + синтез | **Pro** |
| | SMI-скан ВСЕХ конкурентов | 1× `web_search` на каждого | **Flash** |
| **5 Forum Pains**| | | |
| | Извлечение топ-15 болей | парсинг | **Pro** |
| | Отзывы клиента (Яндекс, 2ГИС и др.) | `web_extract` | **Flash** |
| | Отзывы конкурентов (Яндекс.Карты, ProDoctorov, 2ГИС — топ-3) | `web_extract` + тональность | **Pro** |
| | Анализ тональности | синтез | **Pro** |
| **6 Finance** | Выписка ФНС клиента | прямой HTTP (terminal: curl) | **Flash** |
| | Выписка ФНС конкурентов | прямой HTTP (terminal: curl) | **Flash** |
| | Динамика 3-5 лет | расчёт | **Flash** |
| | Margin erosion check | анализ | **Pro** |
| **7 Content Plan** | Боль + тема = формат | синтез Phase 3 + Phase 5 | **Pro** |
| | 4 недели контент-плана | генерация | **Pro** |
| | Запись в data.json | `write_file()` | — |
| **8 HTML Build** | Freshness Gate (tech + SMI + social) | проверка verified_at + re-run | **Flash** |
| | Model Switch Flash→Pro | `hermes config set model` | — |
| | Pre-generation snapshot | `write_file()` JSON | **Flash** |
| | Генерация HTML | `delegate_task` | **Pro** |
| | Post-generation validation (7 пр.) | `head` + `stat` + `grep` | **Flash** |
| | Model Switch Pro→Flash | `hermes config set model` | — |
| **9 QC Critique** | QC1-QC8 × 3 прохода | анализ data.json + HTML | **Pro** |
| | Исправление FAIL | правка data.json | **Pro** |
| **10 Presentation** | Humanizer-russian | чек-лист 27 паттернов | **Pro** |
| | Проверка тире/AI-маркеров | `grep` + чек-лист | **Flash** |
| | Отправка файла | `send_message()` MEDIA: | — |

**Flash** — только механические действия (curl, grep, скрипты, web_search для поиска, Apify запуск)
**Pro** — вся глубина (анализ контента, синтез, форумы, финансы, HTML, тексты, QC)
**—** — модель не участвует (чистый запуск скрипта)

---

## Коммуникация с клиентом (Hard Gate)

**Клиенту не показывать процесс.** Никаких статусов, фаз, номеров шагов, «параллельного выполнения». Только:

1. Приветствие + 1 инсайт через 30 секунд (Immediate Value из Phase 0.5)
2. Молча работа
3. Файл «текущая ситуация: {клиника}.html» + ироничное summary

**Первое сообщение — человеческое, короткое:**
"Анна, здравствуйте! Я Hermes - AI-ассистент AIM. Буду помогать с анализом цифрового присутствия [клиника]. Начинаю сбор данных, всё расскажу по ходу."

**Правило:** если клиент сам спросил «что делаешь?» — ответить одной строкой без технических деталей. Не инициировать показ процесса.

**Почему (июнь 2026):** Владелец клиники не хочет видеть «этапы» — он хочет результат. Показ статусов создаёт ощущение «его грузят работой», а не «ему помогают».

---

## Фаза 0: PRE-FLIGHT (Hard Gate)

**🔴 EXECUTION LOG — загрузка скиллов, проверка инструментов, готовность к бою.**

```
Phase 0 PRE-FLIGHT EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] skill_view('client-onboarding-pipeline')     ЗАГРУЖЕН
[ ] skill_view('social-verifier')                ЗАГРУЖЕН
[ ] skill_view('deep-research-phase-0')          ЗАГРУЖЕН
[ ] skill_view('tech-auditor')                   ЗАГРУЖЕН
[ ] skill_view('humanizer-russian')              ЗАГРУЖЕН
[ ] Проверка: ls /root/bin/ — все скрипты на месте?
      verify-social-accounts.py  find-competitors.py  tg-mtproto.py
      firecrawl-rotate  fc  pm-*.py
[ ] Проверка: python3 /root/.hermes/scripts/apify_actor.py --budget
[ ] Проверка: python3 /root/bin/firecrawl-rotate best
[ ] Проверка: MTProto — туннель жив? (если нет → пометить fallback)
[ ] Проверка: disk space — df -h /root/work/presale/
[ ] Создать директорию: mkdir -p /root/work/presale/{slug}/
[ ] Проверить: browser_navigate работает? (открыть google.com)
─────────────────────────────────
Если любой [ ] пуст → ТИХОЕ уведомление в DM админа.
Работа с клиентом продолжается на доступных инструментах.
НО: все 5 скиллов ОБЯЗАТЕЛЬНЫ. Без них — не начинать.
```

Загрузить скиллы. Проверить скрипты. Проверить Apify. Проверить Firecrawl. Проверить MTProto. Только потом — слово клиенту.

## Фаза 0.5: Deep Research (автономно)
skill_view(name='deep-research-phase-0')

1. Извлечь ВСЕХ врачей с сайта (browser для Bitrix SPA)
2. Классифицировать: star (д.м.н./профессор) / core (к.м.н./главврач) / team
3. Deep research star-врачей (диссертация, профессорство, публикации, СМИ)
4. Исследование клиники (история, рейтинги, лицензии, СМИ)
5. Поверхностный сбор конкурентов (Яндекс.Карты "Похожие места")
6. Верификация соцсетей конкурентов через Google — не доверять handle из данных

**⚠️ Bitrix SPA — doctor URL pattern:** Для сайтов на 1C-Bitrix самый быстрый путь — не SPA-клик по меню, а прямой переход на `/doctors/` (найденный через `web_search site:{domain} врач OR специалист`). Частые URL-паттерны: `/doctors/`, `/vrachi/`, `/specialisty/`, `/about/specialisty/`. Если ни один не работает — browser_navigate на главную, найти меню, клик «Специалисты».

**WOW-фактор: первый инсайт за 30 секунд (Immediate Value):**
Пока собираются данные — отправить клиенту ОДИН сильный инсайт, который видно сразу:
- "У вас 37 врачей, соцсети только у 2 — ваш главный актив не работает"
- "Ваш топ-конкурент на той же улице, а вы его не упоминаете"
- "Ваш основатель — д.м.н. с 20K+ подписчиков, но YouTube не развит"
- "Рейтинг на ProDoctorov 2.6 vs Яндекс 5.0 — разрыв 2.4 балла, это системная проблема"

Правило: 1 инсайт, без деталей, без цифр, чтобы заинтриговать.

Результат -> data.json deep_research

## Фаза 0.75: Audience Analysis (Patient Persona)

**🔴 EXECUTION LOG — кто пациенты, откуда приходят.**

```
Phase 0.75 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Возрастные сегменты определены (дети/взрослые/пожилые)
[ ] Гео: локальные или со всего города?
[ ] Ценовой сегмент: премиум/средний/бюджет
[ ] Каналы привлечения: поиск/соцсети/сарафан/карты
[ ] LTV / repeat rate: сигналы из отзывов
[ ] Confidence: high/medium/low — честно
─────────────────────────────────
Если данных недостаточно → confidence: "low", не додумывать.
Если любой [ ] пуст → СТОП. Фаза не завершена.
```

**Цель:** понять, КТО пациенты клиники — до того, как анализировать врачей и конкурентов.

**Источники данных (по приоритету):**
1. **Яндекс.Метрика** (если доступна через клиента или browser_console на сайте) — демография (возраст, пол, гео), устройства, источники трафика
2. **Google Analytics** (если GA4 ID найден в коде сайта) — то же
3. **Форумы** (Phase 5) — кто пишет? Сами пациенты? Родственники? Возрастная группа по контексту сообщений
4. **Отзывы на картах** — гео отзывов, тематика жалоб/похвал
5. **Сайт клиники** — на какие услуги акцент? Детские/взрослые? VIP/массовый сегмент?

**Что извлечь:**
- **Возрастные сегменты:** дети (педиатрия? детская стоматология?), взрослые (косметология, пластика), пожилые (геронтология)
- **Гео:** локальные пациенты (район) или со всего города/области?
- **Платёжеспособность:** средний чек (сигналы из цен на сайте, из отзывов), VIP-сегмент?
- **LTV / repeat rate:** повторные пациенты или разовые? (сигналы из отзывов: «хожу 5 лет» vs «в первый раз»)
- **Каналы привлечения:** откуда приходят? (поиск, соцсети, сарафан, карты)

**Минимальный результат → data.json:** `audience` — {age_segments: [str], geo: str, price_segment: str, channels: [str], confidence: "high"|"medium"|"low"}

**Если данных недостаточно:** пометить `confidence: "low"` и указать допущения. Не додумывать.

## Фаза 1: Tech Audit (сайт) — многоступенчато
skill_view(name='tech-auditor')

**🔴 EXECUTION LOG — 3 прохода обязательны. Клиент + конкуренты.**

```
Phase 1 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Проход 1: Speed (PageSpeed API + pagespeed.web.dev) 2 источника — КЛИЕНТ
[ ] Проход 1: Speed (PageSpeed API) — ТОП-5 КОНКУРЕНТОВ
[ ] Проход 1: Broken links (15-20 URL)                   ПРОВЕРЕНЫ
[ ] Проход 1: Meta/H1/Alt через web_extract               СОБРАНЫ
[ ] Проход 2: GEO — Medical Schema (browser_console)      ПРОВЕРЕН — КЛИЕНТ
[ ] Проход 2: GEO — robots.txt AI-краулеры (GPTBot, ClaudeBot) ПРОВЕРЕН
[ ] Проход 2: GEO — Medical Schema — ТОП-5 КОНКУРЕНТОВ    ПРОВЕРЕН
[ ] Проход 2: GEO — llms.txt                              ПРОВЕРЕН
[ ] Проход 2: AI-видимость (Perplexity/ChatGPT)           ПРОВЕРЕНА — КЛИЕНТ + КОНКУРЕНТЫ
[ ] Проход 3: Верификация — каждый параметр в 2+ источниках
[ ] СРАВНИТЕЛЬНАЯ ТАБЛИЦА: клиент vs топ-5 конкурентов (Speed, Schema, llms.txt, AI)
─────────────────────────────────
Если любой [ ] пуст → СТОП. Без 3 проходов Phase 1 не завершена.
```

### 1.4 Tech Audit конкурентов (параллельно с клиентом)

Пока собираются данные по клиенту — запустить ТЕ ЖЕ проверки для топ-5 конкурентов:

| Параметр | Для конкурентов |
|----------|----------------|
| Speed (LCP) | PageSpeed API (desktop + mobile) |
| Medical Schema | browser_console — есть JSON-LD с @type MedicalBusiness? |
| llms.txt | web_extract /llms.txt — есть? |
| CMS | browser_console — WordPress/Bitrix/другое? |
| Calltracking | browser_console — Calltouch, Ringostat? |
| Mobile | browser_console на 375×812 — горизонтальный скролл? |

**Результат → сравнительная таблица (WOW-блок для КП):**

| Параметр | VIP Clinic | Конкурент 1 | Конкурент 2 | Конкурент 3 |
|----------|-----------|-------------|-------------|-------------|
| Speed LCP (моб) | ... | ... | ... | ... |
| llms.txt | ✅ | ❌ | ❌ | ❌ |
| Medical Schema | ❌ | ❌ | ❌ | ❌ |
| Calltracking | Calltouch | — | — | — |
| Mobile | ✅ | ... | ... | ... |

**WOW-инсайт:** «У всех конкурентов нет llms.txt — AI-поиск не видит их. Клиент может занять поле первым.» Или: «Конкурент X грузится 8 секунд — клиент в 3 раза быстрее.»

**3 прохода (а не 1):**

*Проход 1 — Сбор (механика):*
- Skill `tech-auditor`: 8 параметров (Speed, Broken links, Meta tags, H1, Alt, Sitemap/robots.txt, SSL, Mobile)
- Bitrix SPA: browser_navigate + browser_console. Не Bitrix: web_extract.
- Прогнать 2 инструмента для скорости: PageSpeed API + WebPageTest (или pagespeed.web.dev)
- Собрать — в data.json `tech_audit.raw`

*Проход 2 — GEO + AI Search Readiness (где клиента НЕ видно):*
- MedicalBusiness Schema (JSON-LD на сайте? @type = MedicalBusiness?)
- FAQPage Schema (есть ли вопросы-ответы в разметке?)
- llms.txt (есть ли /llms.txt? Что там?)
- LocalBusiness Schema (адрес, телефон, часы работы — в разметке?)
- Google Business Profile (заполнен? Часы работы, услуги, фото, посты?)
- Яндекс.Бизнес (заполнен? Активность?)
- 2ГИС профиль (заполнен?)
- Карты: Яндекс.Карты, Google Maps — рейтинг, отзывы, категория
- AI-поиск: web_search site:you.com OR site:perplexity.ai OR site:chatgpt.com "{клиника}" — видят ли AI-поисковики клинику?

*Проход 3 — Верификация (2+ источника):*
- Speed: PageSpeed API vs WebPageTest — совпадают? Если расходятся — перепрогнать 2 раза, взять среднее
- Broken links: head -c на статус 20 ссылок — подтвердить 404
- Meta/H1/Alt: browser_console `document.querySelectorAll(...)` — перепроверить вручную
- GEO-схемы: browser_console `JSON.parse(document.querySelector('script[type="application/ld+json"]')?.textContent)` — проверить существование
- Каждая техцифра: минимум 2 источника

**Результат → data.json:** `tech_audit` — {speed, geo, seo, ai_search, verification_passes: int, method: str, **verified_at: ISO timestamp**}

**Hard Gate Phase 1:** без 3 проходов и верификации — Phase 1 не завершена.

**Freshness Gate (для Phase 8):** перед HTML-генерацией проверить `tech_audit.verified_at`. Если старше 30 минут ИЛИ сессия новая (предыдущий краш) → перепрогнать минимум: Speed (PageSpeed API + pagespeed.web.dev — 2 источника), GEO-схемы (browser_console), Mobile (browser_scroll на 375px). Обновить verified_at. Без этого — не генерировать HTML.

## Фаза 2: Social Verifier (5 проходов)
skill_view(name='social-verifier')

**🔴 EXECUTION LOG — ЗАПОЛНИ ПОСЛЕ КАЖДОГО ПРОХОДА.**

```
Phase 2 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Step 0: verify-social-accounts.py {slug} ЗАПУЩЕН
[ ] Pass 1: Apify Profile Scraper batch (RESIDENTIAL)   ЗАПУЩЕН
[ ] Pass 1 fallback: если Apify 404/все ключи → instagram-fallback-ladder.md
[ ] Pass 2: Google site:instagram.com cross-reference    СДЕЛАН
[ ] Pass 3: Broad search + VK/TG/YouTube/Дзен            СДЕЛАН
[ ] Pass 4: Cross-contamination (кто кого отметил)       СДЕЛАН
[ ] Pass 5: Telegram final sweep через MTProto           СДЕЛАН
─────────────────────────────────
Если Pass 1 дал пустой результат → Pass 2 ОБЯЗАТЕЛЕН.
Если Pass 5 не сделан → СТОП. Фаза не завершена.
```

Step 0: verify-social-accounts.py {slug}

**Fallback Step 0:** если скрипт упал (нет Python, зависимости, API-ключа) — ручная верификация через browser_navigate + web_search `site:instagram.com "{клиника}"`.

5 проходов (RESIDENTIAL proxy, ротация ключей):
1. Apify Profile Scraper batch
2. Google site:search (fallback: Yandex `site:instagram.com` или Bing)
3. Broad search + VK/TG/YouTube/b17.ru/Дзен
4. Cross-contamination (кто кого отметил)
5. Telegram final sweep + мастер-таблица

## Фаза 3: Content Analysis (ключевая ценность)
skill_view(name='social-media-knowledge-base/doctor-content-analysis')

**🔴 EXECUTION LOG — за каждый пункт платят.**

```
Phase 3 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Apify скрап caption'ов (RESIDENTIAL proxy) ЗАПУЩЕН
[ ] Темы контента (3-5) для КАЖДОГО врача с IG     ЕСТЬ
[ ] Формат подачи (шоу/интрига/авторская/школа)     ЕСТЬ
[ ] Топ-пост с цифрами (лайки/просмотры)            ЕСТЬ
[ ] Контентный пробел                               ЕСТЬ
[ ] ER (engagement rate) рассчитан                  ЕСТЬ
[ ] Cross-promo: врач→клиника в bio?                ПРОВЕРЕНО
[ ] Cross-promo: врачи→друг друга?                  ПРОВЕРЕНО
─────────────────────────────────
Если у врача IG >5K, но нет ER → СТОП. Фаза не завершена.
```

Для КАЖДОГО врача с IG/TG/VK:
- Темы контента (3-5 тем из caption 10-12 постов)
- Формат подачи (шоу/сериал, интрига, авторская, школа, до/после)
- Фишка (что отличает)
- Топ-пост с цифрами (лайки, просмотры, комментарии)
- Контентный пробел (чего НЕТ)

Форматы-победители: шоу/сериал (Егорова), интрига (Свиридов), авторская (Кузин), школа (Круглик).

**Кросс-промо врачей и клиники (обязательная проверка):**
1. Проверить: каждый ли врач с IG >5K упоминает клинику в bio/profile?
2. Проверить: отмечают ли врачи клинику в постах (@клиника, #клиника, геолокация)?
3. Проверить: отмечают ли врачи ДРУГ ДРУГА (есть ли сеть взаимного пиара)?
4. Если нет — зафиксировать как gap: "Соцсети врачей не связаны с брендом клиники"
5. Результат → data.json: `doctors[].cross_promo` — {mentions_clinic: bool, mentions_colleagues: bool, notes: str}

**Ключевой сигнал для онбординга:**
Если у клиники 10 врачей с IG >5K, но ни один не упоминает клинику в bio —
клиент платит им зарплату, а их аудитория не знает, где они работают.
Это системная проблема дистрибуции, а не контента.

**Doctor IG Engagement Analysis (обязательный подшаг):**
Для КАЖДОГО врача с Instagram — собрать метрики вовлечённости:
- ER (engagement rate) — средний по последним 20 постам
- Среднее количество лайков и комментариев
- Формула ER: (лайки + комментарии) / подписчики × 100
- Топ-3 поста по ER (что зашло аудитории больше всего)
- Тренд: ER растёт или падает (сравнить первые 10 постов с последними 10)

**Когда Apify заблокирован/не работает:** использовать viewer-сайты (emdigital.ru) или кэшированные данные. Fallback: web_search site:instagram.com "{имя врача}".

**Hard Gate:** без контент-анализа + engagement метрик — не переходить к HTML.

**Founder Brand Gap Diagnosis (для клиник с сильным основателем):**
Сигналы: основатель имеет СМИ (РБК, BBC), научные звания (д.м.н., профессор), но YouTube <5K, TG <1K, остальные врачи без соцсетей. Вывод: контент есть, дистрибуции нет — ключевой аргумент. Результат → data.json: `clinic.founder_brand_gap`.

**Hard Gate:** без контент-анализа -- не переходить к HTML.

## Фаза 3.5: Key Persons + SMI

**🔴 EXECUTION LOG — 4-tier + 4 поиска СМИ.**

```
Phase 3.5 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] 4-tier классификация врачей (star/core/team/hidden)
[ ] SMI-деловые + массовые (12 источников)     ПОИСК ВЫПОЛНЕН
[ ] SMI-глянец (8 источников)                  ПОИСК ВЫПОЛНЕН
[ ] SMI-медицинские (4 источника)              ПОИСК ВЫПОЛНЕН
[ ] Расширенный SMI-поиск без site:            ПОИСК ВЫПОЛНЕН
[ ] Каждая статья — прямой URL (без URL — не факт)
[ ] Vacancy: сайт клиники (web_extract)
[ ] Vacancy: hh.ru employer (browser_navigate)
[ ] Vacancy: конкуренты (browser_navigate)
─────────────────────────────────
Если любой [ ] пуст → СТОП. Фаза не завершена.
```

4-tier классификация:
- Tier 1 (Media Stars): >50K подписчиков
- Tier 2 (Strong): 10K-50K
- Tier 3 (Academic): д.м.н., профессора
- Tier 4 (Hidden): <10K

SMI: 4 параллельных поиска (можно delegate_task для ускорения).

**Запросы:** см. `references/smi-search-queries.md` — Категории 1-4.
Подставить `{query}` = название клиники.
Каждое упоминание -> прямой URL. Без URL -- не факт.

**Расширенный поиск (обязателен, не ограничиваться фиксированным списком):**
```
web_search "{клиника}" интервью OR статья OR эксперт OR рейтинг OR "о клинике" -site:{clinic_domain}
```
Этот запрос без site: находит публикации в СМИ, которые не вошли в 24 фиксированных источника (региональные, нишевые, новые издания, отраслевые блоги). Результат → `smi.unexpected` — массив найденных публикаций из нестандартных источников.

## Фаза 3.6: SMI Placement Map (каналы размещения)

**🔴 EXECUTION LOG — от мониторинга к стратегии размещения.**

```
Phase 3.6 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Загружен smi_media_map.md (read_file)
[ ] Упоминания клиента сопоставлены с картой СМИ
[ ] Упоминания топ-3 конкурентов сопоставлены с картой СМИ
[ ] Gap найден: "конкуренты в Forbes, клиент — нет"
[ ] Приоритетные каналы: 3 СМИ с форматами и why
[ ] Бюджетная оценка: минимальный PR-бюджет на квартал
[ ] Холдинговая структура: Independent Media / Shkulev / RBC
─────────────────────────────────
Если smi_media_map.md не загружен → СТОП.
Если любой [ ] пуст → СТОП. Фаза не завершена.
```

**Цель:** от мониторинга упоминаний → к стратегии размещения. Не просто «о вас пишут здесь», а «вам нужно попасть вот сюда, вот контакты, вот бюджет».

**Источник:** `/opt/data/memories/knowledge/smi_media_map.md` — карта 24+ СМИ с реальными контактами редакций, форматами и бюджетами.

**Метод:**
1. Загрузить файл `smi_media_map.md` (read_file)
2. Сопоставить найденные упоминания клиента (Phase 3.5) с картой — где УЖЕ пишут
3. Сопоставить упоминания топ-3 конкурентов (Phase 4 Step 8.0 + 8.3) — где пишут ОНИ
4. Найти gap: «конкуренты публикуются в Forbes и Vademecum, а вы — нет»
5. Для каждого gap — выбрать формат из карты (интервью, кейс, колонка, спецпроект)

**Что НЕ включать в КП:**
- ❌ Все 24+ контакта списком — перегруз
- ❌ Email'ы редакторов — клиенту не нужны

**Что включать в КП (блок «Белые поля»):**
- ✅ «Ваши конкуренты публикуются в Forbes (реклама), Vademecum (статьи), Marie Claire (герои номера)»
- ✅ «Вот 3 приоритетных канала для вас с форматами: [СМИ] → [формат] → [почему]»
- ✅ Бюджетная оценка: «Минимальный PR-бюджет на квартал: 2 550 000 ₽»

**Для онбординга (закрытая часть для Михаила):**
- Полный список контактов с email'ами (из smi_media_map.md)
- Холдинговая структура: Independent Media (@imedia.ru), Shkulev (@shkulev.ru)
- Рекомендация: начинать с Vademecum (отраслевой, низкий порог входа) и Psychologies (если клиника с психологическим профилем)

**Результат → data.json:** `smi_placement` — {competitor_gaps: [{outlet, format, budget_estimate}], priority_channels: [{outlet, format, contact, rationale}], quarterly_budget_estimate: int, holding_map: {independent_media: bool, shkulev: bool, rbc: bool}}

## Фаза 4: Competitors (системно)
skill_view(name='competitor-scorer')

**🔴 EXECUTION LOG — ЗАПОЛНИ ПЕРЕД ПЕРЕХОДОМ К ШАГУ 1. После каждого шага ставь [x].**

```
Phase 4 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Шаг 1: find-competitors.py {slug} --city "Город"  ЗАПУЩЕН
[ ] Шаг 1 fallback: если find-competitors.py 404 → VC.ru Bayes MedRating (топ-20) + Яндекс.Карты
[ ] Шаг 2: Яндекс.Карты «Похожие места»                browser_navigate ОТКРЫТ
[ ] Шаг 2: блок «Похожие» проскроллен, названия собраны
[ ] Шаг 2: cross-employment врачей (prodoctorov)        web_search СДЕЛАН
[ ] Шаг 2: DocDoc / 2ГИС — список клиник                 СОБРАН
[ ] Шаг 3: Revenue Gap рассчитан
[ ] Шаг 4: Large Group проверен
[ ] Шаг 5: Competitor Clustering сделан
[ ] Шаг 8.0: SMI-скан ВСЕХ конкурентов (по 1 запросу site:)
[ ] Шаг 8.0+: Расширенный SMI-поиск (без site:, широкий web_search)
[ ] 🔴 Шаг 8.1-A: Врачи конкурентов — ПРОХОД 1 (сайт + Apify + Google site:ig)
[ ] 🔴 Шаг 8.1-B: Врачи конкурентов — ПРОХОД 2 (broad search + VK/TG/YouTube/Дзен)
[ ] 🔴 Шаг 8.1-C: Врачи конкурентов — ПРОХОД 3 (cross-contamination: IG клиники конкурента, отметки врачей, browser_navigate)
[ ] Шаг 8.2: Контент-анализ врачей конкурентов (темы/форматы/ER/WOW-дыры)
[ ] Шаг 8.3: SMI топ-3 конкурентов (4 категории, прямые URL)
[ ] Шаг 8.5: WOW-инсайты по каждому конкуренту ВЫВЕДЕНЫ
[ ] ФИЛЬТР: каждый конкурент проверен — точно пластическая хирургия? (не просто косметология)
[ ] ФИЛЬТР: совпадает ценовой сегмент? (премиум/средний/бюджет)
[ ] ФИЛЬТР: >=3 врачей в штате? (отсеять микроклиники)
─────────────────────────────────
Если любой [ ] пуст → СТОП. Фаза не завершена. Не переходи к HTML.
```

**Шаг 1: ProDoctorov Auto-Discovery**
```
python3 /root/bin/find-competitors.py {slug} --city "Город"
```
Скрипт парсит prodoctorov.ru — находит ВСЕ медцентры города, сравнивает с текущей базой, выводит пропущенных.

⚠ Питфолл — city code: Санкт-Петербург = `spb`, не `sankt-peterburg`. Если 404 — browser_navigate для поиска правильного city code.

**Шаг 2: Proximity Sweep — конкуренты рядом**
После ProDoctorov — проверить конкурентов на той же улице / в радиусе 500 м:
- Инструмент: Яндекс.Карты `site:yandex.ru/maps {адрес клиента}` или 2ГИС
- Сигнал: если на той же улице есть многопрофильный центр с 4.5+ рейтингом, которого нет в списке — добавить
- Кейс: КДЦ 24 на Сосновой аллее, 2а — прямо рядом с Детством Плюс, но изначально пропущен

**Шаг 3: Revenue Gap Detection**
После сбора конкурентов — проверить:
```
Если сумма выручек найденных конкурентов < выручки клиента
→ значит пропущен крупный игрок (сигнал для дополнительного поиска)
```
Пример: Детство Плюс (902 млн) vs найденные конкуренты (586 млн) → пропущен Никор (941 млн).

**Шаг 4: Large Group Detection**
Проверить, нет ли в городе крупных групп/сетей, объединяющих несколько юрлиц:
- Признаки: один бренд → несколько юрлиц (стоматология + медцентр), общие учредители
- Суммировать выручку всей группы — может оказаться сопоставимой с клиентом
- Пример: Никор (Никор-2 424 млн + Никор-Н 295 млн + Никор-Мед 222 млн = 941 млн) — почти равен Детству Плюс (902 млн)

**Шаг 5: Competitor Clustering**
Вместо плоского списка — стратегическая кластеризация:
- **Премиум/формат** — дорогой бренд, премиальные интерьеры, высокая наценка
- **Академическая база** — д.м.н. и профессора в штате, научная репутация
- **Узкая специализация** — нишевые игроки с одной сильной услугой
- **Многопрофильный лидер** — широкий спектр, высокая выручка, сеть филиалов
- **Демпинг/агрессивный маркетинг** — низкие цены, массовая реклама

Вывод по каждому кластеру: где клиент сильнее/слабее, где чистое поле.
Результат → data.json: `competitors[].cluster` + rationale.

**Шаг 6: Выписка ФНС топ-5 конкурентов**
Топ-5 конкурентов: выручка, прибыль, сотрудники, ОКВЭД, тренд 3-5 лет.

**Шаг 7: Scorer (5 измерений)**
- Финансовая сила (0-10)
- Соцсети (0-10)
- Качество врачей (0-10)
- Цифровое присутствие (0-10)
- Контент-активность (0-10)

Threat: 40-50 прямой, 30-39 значительный, 20-29 нишевый, <20 не угроза.

**Шаг 8: Deep Competitor Content Analysis (топ-3 по угрозе) — WOW-блок**

**Шаг 8.0: Быстрый SMI-скан ВСЕХ конкурентов (обязателен, до top-3 deep dive)**

Перед углублённым анализом топ-3 — беглый поиск по всем конкурентам (не только топ-3):
- 1 запрос на конкурента: web_search `"{название}" клиника OR врач` без site: (широкий поиск)
- **Дополнительно — расширенный web_search без site:** `"{название конкурента}" интервью OR статья OR эксперт OR рейтинг` — находит публикации в СМИ, не вошедших в фиксированный список (региональные, нишевые, новые издания)
- Фильтр: тема статьи медицина/здоровье/бизнес? Отклоняем: некрологи, криминал, технические заметки
- Результат: `competitors[].smi_quick` — {has_mentions: bool, count: int, top_domain: str, unexpected_sources: [str]}
- Если у конкурента №5 (не топ-3) обнаружены 3+ статьи → поднять его приоритет, включить в топ-3

**Причина:** конкурент №4 с threat=38 может иметь статью в Vogue, но если мы смотрим только топ-3 по Scorer — пропустим.

После Шага 8.0 — продолжить с 8.1 для топ-3 (с учётом возможного повышения приоритета).

### 🔴 8.1: Competitor Doctor 3-Pass Social Verification (Hard Gate)

**Жёсткое правило:** поиск врачей каждого топ-3 конкурента — ровно 3 прохода разными методами. Не нашёл в проходе 1 → проход 2 другим инструментом → не нашёл → проход 3 → только тогда «не найдено».

**Почему одного прохода недостаточно:**
- Google `site:instagram.com "{имя врача}"` пропускает крупные аккаунты (Алифер 135K не показал)
- Apify Profile Scraper требует точного username — без него бесполезен
- Врачи меняют фамилии (замужество), используют никнеймы без фамилии в профиле
- Некоторые врачи принципиально не заводят соцсети — это нужно доказать, а не предположить

**Для каждого топ-3 конкурента — 3 прохода:**

#### ПРОХОД 1: Сайт конкурента + Apify + Google site:instagram.com

1. **Извлечь врачей с сайта конкурента:**
   - `web_extract` на страницы /vrachi, /specialisty, /doctors, /about
   - Bitrix SPA → `browser_navigate` + `browser_console`: извлечь ФИО из DOM
   - Результат: список ФИО + специализаций

2. **Поиск Instagram через Google (для каждого врача):**
   - `web_search "site:instagram.com \"{Фамилия Имя}\" \"{конкурент}\""`
   - `web_search "site:instagram.com \"{Имя Фамилия}\" врач {город}"`
   - Если нашли username → записать, готовить к Apify

3. **Apify Profile Scraper batch (RESIDENTIAL proxy):**
   - Все найденные username'ы — одним batch-запросом
   - Получить: подписчики, посты, ER, bio

4. **Зафиксировать результат:**
   - Найден → `status: "found_pass1"`, username, подписчики
   - Не найден → `status: "not_found_pass1"` → идти в ПРОХОД 2

#### ПРОХОД 2: Broad Search + Все платформы

**Для каждого врача со статусом `not_found_pass1`:**

1. **Широкий поиск (без site:):**
   - `web_search "\"{ФИО}\" врач {город} Instagram"` — без site:instagram.com
   - `web_search "\"{ФИО}\" {специализация} {конкурент}"` — профессиональный контекст
   - `web_search "\"{Фамилия}\" {специализация} отзывы"` — через отзывы пациентов

2. **Альтернативные платформы (не только Instagram):**
   - VK: `web_search "site:vk.com \"{ФИО}\" врач"`
   - Telegram: `web_search "site:t.me \"{ФИО}\""` или MTProto `search`
   - YouTube: `web_search "site:youtube.com \"{ФИО}\" {специализация}"`
   - Дзен: `web_search "site:dzen.ru \"{ФИО}\" {специализация}"`
   - ProDoctorov: `web_search "site:prodoctorov.ru \"{ФИО}\""`

3. **Проверить отзывы пациентов:**
   - На ProDoctorov, Яндекс.Картах, 2ГИС пациенты часто называют врачей по имени
   - `web_extract` страницы отзывов конкурента → поиск упоминаний врачей в тексте

4. **Зафиксировать:**
   - Найден → `status: "found_pass2"`, платформа, username/ссылка
   - Не найден → `status: "not_found_pass2"` → идти в ПРОХОД 3

#### ПРОХОД 3: Cross-Contamination + Browser Deep Dive

**Самый эффективный проход.** Если врач не найден в проходах 1-2, он может быть найден через других людей:

1. **IG клиники конкурента — проверить отметки:**
   - Зайти в IG конкурента через Apify/browser → последние 20 постов
   - Извлечь все @упоминания в caption'ах и комментариях
   - Каждый новый @username → Apify Profile Scraper → bio содержит название конкурента?

2. **IG уже найденных врачей конкурента — проверить их отметки:**
   - Если в проходах 1-2 нашли хотя бы 1 врача → скрап его последних 10-15 постов
   - Извлечь @упоминания коллег в caption'ах
   - **Реальный кейс (Quantum Clinic):** @_doc_annet_cosmetology отметила @dr_gaeva в посте — Гаева не была найдена ни через Google, ни через сайт

3. **Browser deep dive на сайт конкурента:**
   - `browser_navigate` на главную → все страницы со специалистами
   - `browser_console`: `document.body.innerText.match(/[А-Я][а-я]+ [А-Я][а-я]+/g)` — все ФИО на странице
   - Проверить страницы «Акции», «Новости», «Блог» — там часто упоминают врачей
   - Проверить страницы конкретных услуг — там указывают «Приём ведёт: ...»

4. **Финальный вердикт (после 3 проходов):**
   - Найден → `status: "found_pass3"`, метод, username
   - Не найден → `status: "not_found_3passes"` — честно зафиксировать в data.json: «Проверено 3 проходами (сайт+Google+Apify → broad search+VK/TG → cross-contamination+browser) — не обнаружен. Вероятно, врач не ведёт публичные соцсети.»

**После завершения 3 проходов — заполнить [x] в Execution Log:**
- [x] Шаг 8.1-A: ПРОХОД 1 выполнен
- [x] Шаг 8.1-B: ПРОХОД 2 выполнен
- [x] Шаг 8.1-C: ПРОХОД 3 выполнен

**Только после всех трёх [x] переходить к Шагу 8.2 (контент-анализ найденных врачей).**

**Результат → data.json:** `competitors[].key_doctors[]` — {name, specialization, social: {ig: {found: bool, pass: 1|2|3, username, followers}, tg: ..., vk: ..., youtube: ...}, verified_3passes: bool}

8.2. Контент-анализ (по методике Phase 3, но сжато):
- Apify скрап 5-7 постов каждого активного врача
- Темы (3-5), формат, фишка, топ-пост, ER
- Пробел: чего НЕТ в контенте (нет клиники в bio, нет отзывов, нет экспертного контента)

8.3. SMI конкурента: 3+1 параллельных поиска — те же категории, что для клиента.

**Запросы:** см. `references/smi-search-queries.md` — Категории 1-4.
Подставить `{query}` = название конкурента.
Прямые URL статей.

8.4. Соцсети бренда (не врачей):
- IG/TG/VK/YouTube/Дзен самого бренда — подписчики, частота, ER, темы
- Сравнение с клиентом: у кого больше, кто активнее, кто лучше вовлекает

8.5. WOW-инсайты (обязательная выжимка для Phase 10 summary):
Для каждого топ-3 конкурента — 1-2 инсайта, где он проигрывает:
- «Главный врач @nickor_n ведёт IG на 18K, но ни разу не упомянул клинику в bio — его аудитория не знает, где он работает. Это можно забрать»
- «У @medskidka 30K подписчиков, но ER упал с 4% до 1.2% за полгода — формат исчерпал себя»
- «Топ-конкурент на той же улице, но их сайт грузится 8 секунд и не адаптирован под мобильные — GEO-потенциал в минусе»
- «Ни у одного конкурента нет GEO-разметки под AI-поиск (MedicalBusiness Schema, FAQPage, llms.txt) — это чистое поле для клиента»

**Результат → data.json:** `competitors[].deep_analysis` — {key_doctors, content_analysis, smi, social_brand, wow_insight}

**8.6. Многоступенчатая верификация (как для клиента, обязательна для каждого топ-3):**

Проход 1 — Social Verify:
- Каждый IG/TG/VK username конкурента и его ключевых врачей проверить через:
  - Apify Profile Scraper (RESIDENTIAL proxy, batch всех username) — реальные подписчики, ER, активность
  - Google site:instagram.com "{имя врача}" "{конкурент}" — подтверждение существования
- Если Apify не находит аккаунт — Google fallback
- Результат: каждый @username имеет статус verified / not_found / renamed

Проход 2 — Cross-contamination & Brand Attachment:
- Каждый врач конкурента >5K подписчиков:
  - Упоминает ли бренд в bio? (да/нет)
  - Отмечает ли клинику в постах (@клиника, #клиника, геолокация)?
  - Отмечают ли врачи ДРУГ ДРУГА (есть ли сеть взаимопиара)?
- Ключевой инсайт: «у 3 из 5 врачей нет ссылки на клинику в bio — их 50K подписчиков не конвертируются в пациентов»

Проход 3 — Верификация цифр (2+ источника):
- Подписчики: Apify данные vs SocialBlade/Inflact vs Google кэш
- ER: Apify данные vs ручной подсчёт по 3-5 последним постам
- СМИ: URL статьи открывается? Дата актуальна?
- Если не верифицировано — пометить как «оценка» с указанием источника

Проход 4 — QC мини-цикл (внутри Phase 4):
- Если у любого из топ-3 конкурентов нет verified @username хотя бы для 1 врача — добрать
- Если WOW-инсайты не выведены — вернуться к 8.5
- Максимум 2 микро-цикла на Phase 4 (Goal Loop)

**Результат верификации → data.json:** `competitors[].deep_analysis.verification` — {social_verified: bool, cross_promo_checked: bool, sources_verified: bool, gaps_remaining: [str]}

**8.7. Tech Audit конкурентов (как Phase 1, но для топ-3):**

⚠️ Если tech-аудит конкурентов УЖЕ сделан в Phase 1 (сравнительная таблица клиент vs топ-5), то здесь — ТОЛЬКО дополнить параметрами, не вошедшими в Phase 1: Google Business Profile, Яндекс.Бизнес, 2ГИС.

Для каждого топ-3 конкурента — сжатый Tech Audit (3 прохода, как в Phase 1):

*Проход 1 — Сбор:*
- Speed: PageSpeed API (desktop + mobile) — LCP, FID, CLS
- Broken links: head -c на 5 ключевых страниц (главная, услуги, врачи, цены, контакты)
- Meta tags, H1, Alt — поверхностно (главная + 1-2 внутренних)
- CMS детекция: Bitrix/SPA? Кто хостинг?
- Телефоны/Calltracking: Calltouch, Ringostat — есть ли?
- Аналитика: Яндекс.Метрика, Google Analytics, GA4 — есть ли в коде?
- SSL + Mobile (скролл на телефоне)

*Проход 2 — GEO конкурента:*
- MedicalBusiness Schema есть?
- Google Business Profile заполнен? Категория? Посты?
- Яндекс.Бизнес / 2ГИС — рейтинг, отзывы, заполненность
- llms.txt есть?
- AI-поиск: видит ли Perplexity/ChatGPT/Gemini конкурента?

*Проход 3 — Сравнение с клиентом:*
- Сравнительная таблица: клиент vs конкурент 1 vs конкурент 2 vs конкурент 3
- Параметры: Speed (LCP), GEO-схемы, AI-видимость, CMS, Calltracking, Google Business заполненность, Яндекс.Карты рейтинг
- Кто выигрывает по каждому параметру?

**Результат → data.json:** `competitors[].tech_audit` — {speed, geo_schema, ai_search, gbp, yandex_business, cms, calltracking, analytics, comparison: {client_wins: [str], competitor_wins: [str]}, gaps: [str]}

**WOW-инсайт из техсравнения:**
- «Конкурент X грузится 8 секунд, а клиент — 2.5 — возьмём это в GEO-стратегию»
- «Ни у одного конкурента нет llms.txt — AI-поиск не видит их. Клиент может занять поле первым»
- «У всех конкурентов Calltouch, у клиента — нет — теряет 30% звонков»

**Competitor Source Gate (Post-Mortem VIP Clinic, июнь 2026):**

Агент склонен выдумывать конкурентов из web_search без проверки. Результат на VIP Clinic: Frais Clinic, Beauty Doctor, Esthetic Clinic — ИНН неверны, клиник не существует. DocDoc показал 21 реальную клинику.

**Жёсткое правило:** ПЕРЕД записью в data.json проверить КАЖДОГО конкурента через DocDoc/ProDoctorov/Яндекс.Карты. Если не подтверждён — удалить.

**Hard Gate Phase 4:** без deep_analysis топ-3 конкурентов + tech_audit топ-3 — Phase 4 не завершена.

## Фаза 5: Forum Pains + Reviews

**🔴 EXECUTION LOG — форумы + отзывы + тональность.**

```
Phase 5 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Woman.ru — поиск по названию клиники + "отзыв"
[ ] IRecommend — поиск, есть ли карточка клиники
[ ] Pikabu — поиск упоминаний
[ ] ProDoctorov — рейтинг, кол-во отзывов, тональность (≥20 отзывов)
[ ] Яндекс.Карты — рейтинг, кол-во отзывов, скорость ответа
[ ] НаПоправку — рейтинг, жалобы
[ ] Тональность: позитив/нейтрально/негатив в % (минимум 20 отзывов)
[ ] Тренд: растёт/падает рейтинг за 3-6-12 мес
[ ] Скорость ответа клиники: часы/дни/не отвечают
[ ] Топ-3 проблемы из негатива + цитаты
[ ] Топ-3 преимущества из позитива
[ ] 🔴 КОНКУРЕНТЫ: Яндекс.Карты — рейтинг, кол-во отзывов (топ-3)
[ ] 🔴 КОНКУРЕНТЫ: ProDoctorov — рейтинг, тональность (топ-3)
[ ] 🔴 КОНКУРЕНТЫ: 2ГИС — рейтинг, отзывы (топ-3)
[ ] 🔴 КОНКУРЕНТЫ: общие боли пациентов → сигналы для WOW-инсайтов
─────────────────────────────────
Если любой [ ] пуст → СТОП. Фаза не завершена.
```

Зависит от ниши:
- Пластика/косметология: Woman.ru, IRecommend, Pikabu, MedAboutMe
- Психология: b17.ru (форум), Woman.ru Психология
- Стоматология: Yell, Zoon, ProDoctorov

**⚠️ Нишевый паттерн — премиум-клиники (anti-age/косметология):**
Для премиальных клиник антивозрастной медицины и косметологии (ARclinic, Luaclinic, Code of Beauty) потребительские форумы (Woman.ru, Pikabu, IRecommend) часто возвращают 0 результатов. Это НЕ означает провал исследования — это сигнал ниши. Пациенты этого сегмента оставляют отзывы на Яндекс.Картах (304+), ProDoctorov (100+), 2ГИС (89+), а не на форумах для широкой аудитории. В data.json `forum_pains` — честно указать `found: false` с пометкой «для данной ниши основные отзывы на специализированных платформах, форумы нерелевантны».

Что собрать: топ-15 болей с тональностью, цитаты, кол-во ответов. Если форумы пусты — не считать это gap'ом, зафиксировать как особенность ниши.

Отзывы: Яндекс.Карты, ProDoctorov, 2ГИС, DocDoc.

**Метрики анализа отзывов (обязательные):**
1. Общий рейтинг по платформам (средневзвешенный)
2. Тональность — метод: ручная классификация по ключевым словам и контексту. Минимум 20 отзывов с платформы. Шкала: позитив (хвалят врача/клинику/результат), нейтрально (информационные), негатив (жалобы на сервис/качество/цену). Проценты от общего числа проанализированных.
3. Тренд динамики (растёт/падает рейтинг за 3-6-12 месяцев)
4. Скорость ответа клиники на отзывы (часы/дни/не отвечают)
5. Ключевые проблемы из негативных отзывов (топ-3)
6. Ключевые преимущества из позитивных (топ-3)

**Сигнал разрыва:** если ProDoctorov 2.6, а Яндекс 5.0 (разброс >1.5 балла) —
системный сигнал: на одной платформе клинику топят, на другой хвалят.
Требует отдельного анализа: кто пишет, как отвечает клиника, есть ли накрутка.

Результат → data.json: `reviews_analysis` — {
    platforms: {prodoctorov: {rating, tone, trend, response_time},
                yandex: {...}, 2gis: {...}, docdoc: {...}},
    gaps: ["ProDoctorov 2.6 vs Яндекс 5.0 — разброс 2.4 балла"]
}

## Фаза 6: Finance (клиент + конкуренты)
skill_view(name='financial-fetcher')

**🔴 EXECUTION LOG — выписка ФНС клиента + топ-5 конкурентов.**

```
Phase 6 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Клиент: ИНН найден (web_search / data.json)
[ ] Клиент: прямой HTTP к egrul.nalog.ru (2-шаг: POST→токен→GET) — выписка ФНС
[ ] Клиент: выручка, прибыль, сотрудники, ОКВЭД — 3-5 лет
[ ] Клиент: margin erosion check (прибыль падает при росте выручки?)
[ ] Топ-5 конкурентов: ИНН найдены для каждого
[ ] Топ-5 конкурентов: выписка ФНС (прямой HTTP)
[ ] Топ-5 конкурентов: выручка/прибыль/ОКВЭД для каждого
[ ] Сравнительная таблица: клиент vs топ-5 по выручке и марже
─────────────────────────────────
Если прямой HTTP заблокирован → Rusprofile (web_extract).
Если Rusprofile недоступен → web_search "выручка ИНН".
Fallback помечать: "данные ФНС не верифицированы".
Если любой [ ] пуст → СТОП. Фаза не завершена.
```

**Основной метод:** прямой HTTP к egrul.nalog.ru (2-шаговый: POST с ИНН → получаем токен → GET search-result/{token} → JSON с выручкой/прибылью). **БЕЗ браузера** — HTTP работает мгновенно (0.1-0.2 сек), browser не нужен.

**Fallback 1:** Rusprofile — web_extract `rusprofile.ru/search?query={ИНН}` для извлечения выручки, прибыли, сотрудников.

**Fallback 2:** web_search `"выручка" "{название компании}" ИНН` — данные из открытых источников (РБК Компании, Spark, Контур.Фокус).

**⚠️ Важно:** curl на egrul.nalog.ru блокируется CAPTCHA. Использовать ТОЛЬКО browser_navigate. Запрещённый термин: «EGRUL» → «выписка ФНС» в тексте клиенту.

Для клиента: выписка ФНС -> выручка, прибыль, сотрудники, ОКВЭД, 3-5 лет динамики.
Для топ-5 конкурентов: то же.

Проверка: не падает ли прибыль при росте выручки (margin erosion vs схема).

## Фаза 7: Content Plan (супер-темы) — ЗАПРЕЩЕНО ПРОПУСКАТЬ. Выполнить до Phase 8. Без контент-плана HTML НЕ генерировать.

**🔴 EXECUTION LOG — каждый слой данных должен быть использован.**

```
Phase 7 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Phase 5 данные ЗАГРУЖЕНЫ: forum_pains (топ-15 болей + тональность)
[ ] Phase 4 данные ЗАГРУЖЕНЫ: competitor content (темы/форматы/WOW)
[ ] Трендвотчинг: web_search по нише + сезону
[ ] Content Navigator применён:
     [ ] Сегменты аудитории (из Phase 0.75) → портрет: боли/ценности/возражения
     [ ] TOFU/MOFU/BOFU структура (знакомство → доверие → продажа)
     [ ] Адаптация под КАЖДУЮ соцсеть (TG ≠ VK ≠ IG ≠ Дзен ≠ YouTube)
[ ] 4 недели: TOFU → MOFU → BOFU → TOFU (образование)
[ ] Каждая тема: канал + формат (пост/Reels/статья) + ответственный врач
[ ] Revenue Impact Calculator: потенциал в деньгах РАССЧИТАН
─────────────────────────────────
Если любой [ ] пуст → СТОП. Не переходи к HTML.
```

### 7.1 Слои данных (обязательные входы)

Перед генерацией тем — загрузить ОБЯЗАТЕЛЬНО:

**Слой 1: Боли форумов (Phase 5)**
Из `data.json → forum_pains`:
- Топ-15 болей пациентов (из Woman.ru, ProDoctorov, IRecommend, Pikabu)
- Тональность: позитив/нейтрально/негатив в процентах
- Цитаты пациентов (для живых хуков)
- Скорость ответа клиники на отзывы

**Слой 2: Контент конкурентов (Phase 4)**
Из `data.json → competitors[].deep_analysis`:
- Темы, которые уже освещают конкуренты (не дублировать, а БИТЬ сильнее)
- Форматы конкурентов и их ER (где проигрывают — туда и бить)
- WOW-инсайты: чего у конкурентов НЕТ (пустые ниши)
- SMI конкурентов: где они публикуются, а клиент — нет

**Слой 3: Трендвотчинг**
- `web_search "{ниша} {сезон} {год} тренды"` — что сейчас обсуждают
- Проверить Яндекс.Вордстат (если есть доступ) по топ-запросам ниши
- Учесть сезонность (декабрь/март/июнь/сентябрь)

### 7.2 Методика Content Navigator (применяется к каждому слою)

**Шаг А — Сегменты аудитории (из Phase 0.75):**
Из `data.json → audience` берём возрастные сегменты, гео, ценовой сегмент.
Для КАЖДОГО сегмента — короткий портрет: кто, боль, ценность, возражение.

**Шаг Б — TOFU/MOFU/BOFU раскладка:**
- Неделя 1 (TOFU — знакомство): темы на основе БОЛЕЙ ФОРУМОВ + трендвотчинга. Человек узнаёт себя → подписывается.
- Неделя 2 (MOFU — доверие): темы на основе КОНТЕНТА КОНКУРЕНТОВ. Показываем то, чего у них нет. Экспертиза врача.
- Неделя 3 (BOFU — продажа): темы-услуги. Мягкий переход к записи на приём. Форматы: кейсы, до/после, интервью с пациентом.
- Неделя 4 (TOFU/MOFU — образование): авторские методики, конгрессы, научные публикации. Закрепление: «эти врачи — лучшие».

**Шаг В — Адаптация под соцсеть (для КАЖДОЙ темы):**
- Instagram: Reels (15-30 сек) + карусель + Stories. Хук через любопытство/узнавание. Визуал обязателен.
- Telegram: пост 500-1000 знаков. Опросы, кружочки. Живой тон.
- VK: длинный пост + VK Клипы. Статьи с SEO-ключами.
- YouTube: Shorts (нарезка из Reels) + полное видео для MOFU/BOFU тем.
- Дзен: статья 2000-4000 знаков. Цепляющий заголовок. SEO-текст с ключами.

**Шаг Г — Анти-штампы (Content Navigator quality control):**
- ❌ «уникальное предложение», «лучший выбор», «не упустите шанс»
- ❌ Хуки через страх, тревогу, провокацию
- ✅ Хуки через любопытство, узнаваемость, реальный момент
- ✅ Конкретика: цифры, имена врачей, реальные кейсы

### 7.3 Формат выдачи (для каждой темы)

```
Неделя 1 (TOFU, июнь) → «Почему губы после филлера выглядят неестественно?»
  Боль: форум Woman.ru — «перестала улыбаться после увеличения губ» (цитата)
  Тренд: #естественнаякрасота — рост запросов за месяц
  Конкуренты: МОЛЧАТ об этой проблеме (WOW-gap)
  Формат: Reels (15 сек) — врач показывает на модели зоны безопасности
  Канал: IG (@drkruglik) → TG → VK Клипы → Дзен (статья-разбор)
  Врач: Сергей Круглик
  CTA: «Хотите узнать, подходит ли вам эта процедура? → запись в Direct»
```

### 7.4 Revenue Impact Calculator

Оценка потенциала ТОЛЬКО от реальных данных:
- **GEO-трафик:** если схем нет → потенциал = средний органик × конверсия × средний чек (или «оценка невозможна без данных»)
- **Контент врачей:** Σ(подписчики × ER × 0.01) × средний чек
- **Отзывы:** +0.1⭐ рейтинга = +0.8% конверсии (NRC Health)

Если данных недостаточно → «требуются данные от клиента: средний чек, трафик, первичные пациенты/мес».

**Дистрибуция контента (обязательный подшаг):**
Для каждой единицы контента — определить каналы дистрибуции:
- Instagram: рилсы + истории с отметками врачей (@dr.x) и клиники (@клиника)
- Telegram: пост в канале клиники + репост врачами в личные каналы
- VK: клип (VK Клипы) + статья с ссылкой на сайт
- YouTube: Short (нарезка) + полное видео на канале клиники/врача
- Дзен: статья, переработанная из видео/рилса (SEO-текст с ключами)

**Hard Gate:** у каждой единицы контента в контент-плане указан канал +
ответственный врач. Если канал не указан — контент не засчитывается.

**Сезонность контента (обязательный параметр):**
Каждый пункт контент-плана привязать к сезону/месяцу:
- Декабрь-февраль: зимние процедуры (коррекция после отпусков, подготовка к сезону)
- Март-май: весеннее обновление, подготовка к лету
- Июнь-август: летние акции, реабилитация, процедуры в отпуске
- Сентябрь-ноябрь: деловой сезон, возвращение в город, осенние акции

Формат строки контент-плана: "Неделя 1 (скепсис, декабрь) → тема → канал → ответственный врач"

**Revenue Impact Calculator (оценка потенциала — ТОЛЬКО от реальных данных клиента):**

Каждая цифра должна быть выведена из конкретных данных в data.json:

- **GEO-трафик:** `data.tech_audit.geo` содержит наличие/отсутствие схем. Если схем нет — потенциал = средний органик-трафик ниши × средняя конверсия × средний чек. Цифры органик-трафика брать из PageSpeed API или Яндекс.Метрики клиента (если доступна). Если трафик неизвестен — НЕ писать цифру, указать: «оценка невозможна без данных по трафику».

- **Контент врачей:** `data.doctors[]` содержит `followers` и `er` для каждого врача с соцсетями. Потенциал = Σ(подписчики_врача × ER_врача × 0.01) × средний чек. Коэффициент 0.01 (1% от вовлечённой аудитории) — консервативная оценка. Если ER неизвестен — не считать.

- **Отзывы:** разница между максимальным и текущим рейтингом на ProDoctorov × данные о конверсии из открытых исследований (NRC Health: +0.1⭐ = +0.8% конверсии). Если рейтинг не собран — не считать.

**Жёсткое правило:** если хотя бы один множитель в формуле не получен из реальных данных клиента — этот пункт калькулятора пропускается с пометкой «данных недостаточно». Никаких generic 20-40%.

Пометка: "сырой контент-план, для стратегии отдельный документ".

## Фаза 8: HTML Build
skill_view(name='html-kp-generator')


### 8.0: Определение режима (ОБЯЗАТЕЛЬНЫЙ ПЕРВЫЙ ШАГ)

**ЗАПРЕЩЕНО** начинать генерацию без явной установки режима.

| Режим | Блок 12 | Тон | CTA |
|-------|---------|-----|-----|
| `presale` | Оффер/CTA (AIM предлагает) | Продающий | Есть |
| `onboarding` | Рекомендации (без AIM) | Партнёрский | Нет |

**Определение режима:**
- Контекст содержит "presale" или цель чата = продажа → `presale`
- Клиент уже платит или контекст содержит "онбординг" → `onboarding`
- Неясно → запросить уточнение у пользователя тихим уведомлением

**Hard Gate:** если MODE=onboarding и в HTML обнаружен Оффер/CTA или "AIM предлагает" → заблокировать отправку, регенерировать.


**Model Switch — принудительное переключение на Pro (Hard Gate):**
Перед любым действием в Phase 8:
```
# Сохранить текущую модель
current_model=$(hermes config show 2>&1 | grep -A5 "Model:" | grep "model:" | head -1 | sed "s/.*'model': '//" | sed "s/'.*//")

# Переключить на Pro
hermes config set model "deepseek/deepseek-v4-pro"

# ... генерация HTML ...

# Вернуть обратно (только после успешной генерации)
hermes config set model "$current_model"
```

Если `current_model` уже Pro — не переключать.
Если переключение не удалось — продолжить на Flash. Использовать шаблон client-kp-template.html.

**Pre-generation snapshot:**
Перед генерацией HTML — сохранить ВСЕ собранные данные в `/root/work/onboarding/{slug}/pre-html-snapshot.json`:

Структура снапшота:
```json
{
  "ts": "ISO timestamp",
  "slug": "slug клиента",
  "phases_completed": ["phase0", "phase1", "phase2", "phase3", "phase3.5", "phase4", "phase5", "phase6", "phase7"],
  "gaps_remaining": ["vacancy_intel_not_collected", ...],
  "data_summary": {
    "doctors_total": 15,
    "doctors_with_social": 3,
    "competitors_found": 10,
    "competitors_with_finance": 5,
    "forums_scraped": true,
    "smi_articles_with_url": 8,
    "content_analysis_done": true
  }
}
```

Назначение снапшота: если HTML сгенерируется с ошибкой (0 байт, битый файл) — восстановить можно из JSON без повторного сбора данных.

**🔴 EXECUTION LOG — каждая проверка перед генерацией.**

```
Phase 8 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Freshness Gate: tech_audit.verified_at свежий?      ПРОВЕРЕНО
[ ] Pre-generation snapshot сохранён                     ЕСТЬ
[ ] Model Switch на Pro (если ещё не Pro)                СДЕЛАНО
[ ] PRE-BUILD CHECKLIST (11 пунктов)                     ВСЕ ✅
[ ] data.json содержит 14+ секций                        ПРОВЕРЕНО
[ ] Post-generation: head -c 20 → DOCTYPE                ПРОВЕРЕНО
[ ] Post-generation: stat → >0 байт                      ПРОВЕРЕНО
[ ] Post-generation: grep — → 0                          ПРОВЕРЕНО
[ ] Post-generation: grep DPI → >0                       ПРОВЕРЕНО
[ ] Post-generation: grep AI Card → >0                   ПРОВЕРЕНО
[ ] Post-generation: grep 'http' в блоке СМИ → каждая статья клиента с URL
[ ] Post-generation: grep 'http' в блоке Конкуренты → SMI конкурентов с URL
[ ] Post-generation: grep 'темы\|формат\|ER\|WOW' в блоке Конкуренты → контент-анализ виден
─────────────────────────────────
Если любой [ ] пуст → СТОП. Не отправлять.
```
- [ ] Контент-анализ врачей: скрап IG каждого
- [ ] СМИ-ссылки: прямые URL статей
- [ ] Цифры верифицированы (Apify/ФНС/Rusprofile)
- [ ] Instagram клиники жив
- [ ] Instagram врачей верифицирован
- [ ] verify-social-accounts.py **повторно запущен (forced re-run)** перед сборкой — все ✅. Если скрипт недоступен: ручная верификация через browser_navigate + web_search site:instagram.com
- [ ] Cross-promo врачей проверен (bio/mentions)
- [ ] Digital Presence Index рассчитан (7 компонентов)
- [ ] Revenue Impact Calculator от реальных данных (не generic)
- [ ] Phase 7 Content Plan ВЫПОЛНЕН — контент-план на 4 недели готов, данные в data.json
- [ ] Tech audit клиента перепроверен (Speed 2 ист., GEO browser_console, verified_at свежий)
- [ ] SMI клиента перепроверено (3 поиска) — свежесть данных подтверждена

12 блоков КП (для presale):
1. Hero (4 метрики)
2. О клинике
3. Рынок/Финансы (сравнение с конкурентами)
4. Эксперты (топ-10 с соцсетями)
5. Контент-анализ (темы/форматы/пробелы)
6. СМИ (прямые URL)
7. Конкуренты
8. Белые поля
9. Digital Presence Map
10. GEO (AI Search) — разметка под нейросети:
    - MedicalBusiness Schema — тип организации для Google AI, Knowledge Panel, SGE
    - FAQPage Schema — ответы на топ-15 вопросов пациентов (отображаются в AI Overview)
    - llms.txt / llms-full.txt — индекс для AI-ассистентов (GPT, Claude, Gemini)
    - Правило первых 50 слов — максимум ключевой информации в заголовке + лиде (AI-поиск читает начало)
    - Естественно-языковые запросы — оптимизация под голосовой поиск и разговорные интенты
    - Локальный GEO — Google Business Profile, Яндекс Бизнес, 2ГИС, Zoon
    - Patient Intent Map — карта интентов: какие запросы ведут к записи на приём
11. Контент-план (сырой)

12 блоков онбординга (клиент уже платит — то же, но БЕЗ блока 12 (Оффер/CTA). Вместо него — блок «Рекомендации» (без продажи AIM).

**Digital Presence Index (WOW-метрика):**
Сводный индекс цифрового присутствия клиники (0-100), автоматически собираемый из:
- Instagram (подписчики + ER) — 25 баллов
- Telegram (подписчики + активность) — 20 баллов
- VK (подписчики + ER) — 15 баллов
- YouTube (подписчики + частота) — 15 баллов
- Дзен (подписчики) — 5 баллов
- Сайт (PageSpeed + Mobile) — 10 баллов
- Отзывы (средний рейтинг по платформам) — 10 баллов

Сравнение с топ-3 конкурентами. Вывод: "Ваш DPI — 34/100.
Среднее по рынку — 22/100. Вы сильнее, но отрыв сокращается."

**AI Capabilities Card (WOW-блок):**
В финальный отчёт добавить блок "Что сделано за [X] минут нейросетью":
- Проанализировано сайтов: Y
- Найдено конкурентов: Z
- Проверено соцсетей врачей: N
- Собрано отзывов: M
- Изучено форумных тем: K
- Сгенерировано рекомендаций: P

Цифры — реальные из data.json. Формат: визуальная карточка с иконками.

**HARD RULE:**
- presale — 12 блоков включая Оффер/CTA
- онбординг — 11 блоков, блок 12 = Рекомендации, никакой продажи AIM
- проверка перед отправкой: если режим=онбординг и есть Оффер/CTA или «AIM предлагает» — заблокировать отправку

**Post-generation validation (7 проверок):**
1. `head -c 20 index.html` → `<!DOCTYPE html>` (не битый)
2. `stat --format=%s index.html` → >0 (не 0 байт)
3. `grep -c '—' index.html` → 0 (длинные тире — ZERO)
4. `grep -c 'контент-анализ\|content-analysis\|СМИ\|рекомендац' index.html` → >0
5. Каждый блок 1-11 присутствует в структуре DOM
6. `grep -c 'Digital Presence Index\|DPI' index.html` → >0 (WOW-метрика есть)
7. `grep -c 'нейросет\|AI.*минут\|сделано за' index.html` → >0 (AI Capabilities Card есть)

Если любой FAIL — не отправлять, regenerate.

ДИЗАЙН (ЖЁСТКО): v3 ripple-expand анимация — 5 точек падения × 3 кольца, расширяются от 0 до 700px с cubic-bezier(0.4,0,0.2,1). Полный CSS и HTML в `html-kp-generator/templates/aim-offer-template.html` и `html-kp-generator/references/ripple-expand-css.md`. НЕ использовать client-kp-template.html (там старые статические кольца ring-lg-* / ring-pulse-*).

## Фаза 9: QC Critique (3 прохода) — ЗАПРЕЩЕНО ПРОПУСКАТЬ. Выполнить ПОСЛЕ Phase 8. Без QC HTML НЕ отправлять клиенту.

**🔴 EXECUTION LOG — 10 проверок × 3 прохода.**

```
Phase 9 EXECUTION LOG (Hard Gate):
─────────────────────────────────
ПРОХОД 1:
[ ] QC1: Telegram — реально активен? (MTProto/web_search)
[ ] QC2: IG cross-contamination — все врачи найдены через отметки?
[ ] QC3: Финансы конкурентов — из ФНС/Rusprofile, мин 3 с цифрами?
[ ] QC4: Форумы — Woman.ru, IRecommend, Pikabu собраны?
[ ] QC5: Контент-анализ — темы/форматы/ER/топ-пост каждого врача?
[ ] QC6: Все соцсети — IG, TG, VK, YouTube, Дзен — все 5 проверены?
[ ] QC7: Верификация — multi-source для подписчиков/финансов?
[ ] QC8: СМИ — 4 категории, прямые URL каждой статьи?
[ ] QC9: Deep Competitor — контент врачей конкурентов + WOW?
[ ] QC10: Tech Audit — клиент + топ-3, сравнительная таблица?
[ ] Исправить все FAIL → ПРОХОД 2

ПРОХОД 2:
[ ] Повторить QC1-QC10 по исправленным данным
[ ] Исправить оставшиеся FAIL → ПРОХОД 3

ПРОХОД 3:
[ ] Финальная верификация QC1-QC10
[ ] Все [x] → файл готов к отправке
─────────────────────────────────
Если любой QC FAIL после 3 проходов → честно в gaps.
Если QC4 (форумы) пуст для премиум-клиник → "нишевый паттерн".
Без 3 проходов HTML НЕ отправлять.
```


**Единый чеклист (10 проверок):** PRE-BUILD в Phase 8 = pre-check (данные собраны?). QC в Phase 9 = post-check (в HTML всё попало?). Не выполнять дважды.

После КАЖДОГО прохода:

| Критерий | Что проверяем |
|----------|---------------|
| QC1 Telegram | Реально активен? Через MTProto, не "кажется" |
| QC2 IG cross-contamination | Все врачи найдены? Отметки в постах? |
| QC3 Финансы конкурентов | Из ФНС/Rusprofile, мин 3 с цифрами |
| QC4 Форумы | Woman.ru, IRecommend, Pikabu. data.json содержит forum_pains с топ-15 болей? |
| QC5 Контент-анализ | Темы/форматы/топ-пост/пробел каждого врача. data.json содержит content_analysis? |
| QC6 Все соцсети | IG, TG, VK, YouTube, Дзен — все 5 площадок проверены |
| QC7 Верификация | Multi-source (подписчики/ER/финансы — обязательно 2+ источника). Single-source (GEO-схемы/llms.txt/SEO-теги — 1 источник, помечать «верифицировано: 1 источник») |
| QC8 СМИ | 4 категории (см. `references/smi-search-queries.md`). Каждая статья — прямой URL |
| QC9 Deep Competitor Analysis | Топ-3 конкурента: Competitor Doctor 3-Pass (8.1-A/B/C) выполнен? Все 3 прохода пройдены? Контент-анализ врачей сделан? WOW-инсайты выведены? Каждая цифра (подписчики, ER, статьи) в 2+ источниках? |
| QC10 Tech Audit (клиент + конкуренты) | Phase 1: 3 прохода пройдены? GEO/AI-глубина сделана? Speed верифицирован (2+ источника)? Phase 4: tech_audit топ-3 конкурентов сделан? Сравнительная таблица клиент vs конкуренты есть? |

**Goal Loop для Phase 4:** если после QC9 остались gaps (нет deep_analysis хотя бы у 2 из 3 конкурентов, WOW-инсайты не выведены) или QC10 не пройден (нет tech_audit топ-3, нет сравнительной таблицы) — вернуться к Phase 4 Шаг 8-8.7, добрать данные. Максимум 2 цикла.

Автомат: проход -> QC -> исправить -> проход -> QC -> исправить -> проход -> QC -> финал -> отправить.

## Фаза 10: Presentation + Auto-Delivery

**🔴 EXECUTION LOG — humanizer + проверка + отправка.**

```
Phase 10 EXECUTION LOG (Hard Gate):
─────────────────────────────────
[ ] Humanizer-russian применён (27 паттернов + душа)
[ ] Проверка: grep '—' → 0 длинных тире
[ ] Проверка: запрещённые термины (EGRUL, мертвечина)
[ ] Проверка: директивный тон («научим», «починим»)
[ ] Проверка: ссылки полным URL (не @username)
[ ] Проверка: СМИ клиента — каждая публикация с http-ссылкой
[ ] Проверка: СМИ конкурентов — каждая публикация с http-ссылкой
[ ] Проверка: блок Конкуренты — видны их темы/форматы/ER/WOW-дыры
[ ] Проверка: grep -c 'http' в секции СМИ >= кол-ва статей клиента + конкурентов
[ ] Имя файла: "текущая ситуация: {клиника}.html"
[ ] Отправка: send_message() с MEDIA: — БЕЗ вопроса
[ ] Summary: 7-9 пунктов + "На что обратили внимание" (только конкуренты)
[ ] Action Plan: 4 блока (quick wins / месяц 1 / месяц 2-3 / квартал)
[ ] Action Plan: каждый пункт привязан к цифре из data.json
[ ] Action Plan: сроки календарные, бюджет из Phase 3.6
[ ] Отправка: файл + summary + action plan — ОДНОЙ пачкой
─────────────────────────────────
Если любой [ ] пуст → СТОП. Не отправлять.
```

1. Применить humanizer-russian (10 пунктов)
2. Проверить: 0 длинных тире, 0 AI-маркеров, 0 директивного тона

**3. Файл клиенту — автоматически, без вопроса (Hard Gate):**
- Имя файла: «текущая ситуация: {название клиники в нижнем регистре}»
  (например: `текущая ситуация: арт-клиник.html` или `текущая ситуация: детство плюс.html`)
- Путь: файл из Phase 8 (index.html) — скопировать с правильным именем
- Отправка: `send_message()` с MEDIA:путь в чат клиента
- БЕЗ запроса разрешения. Совсем. Никогда.

**4. Summary после файла (обязательно):**
Сразу после отправки файла — краткое текстовое сообщение в тот же чат.

Формат:
- Ироничный, располагающий тон («забирайте», «ничего себе», «нормальная больничка»)
- 7-9 пунктов ключевых находок (без воды)
- Каждый пункт — 1 короткая строка, максимум 2
- Последние 1-2 пункта — обязательный раздел «На что обратили внимание» — только про КОНКУРЕНТОВ (их косяки, слабые места)
- Ни одного косяка клиента в этом разделе

**5. Post-Onboarding Action Plan (ОБЯЗАТЕЛЬНО — сразу после summary)**

Это не «спасибо, до свидания». Это карта того, что делать дальше. Клиент платит не за отчёт — он платит за план действий.

Структура — 4 блока, продуманных трижды (cross-check с данными, конкурентами и бюджетом):

```
📋 ЧТО ДЕЛАТЬ ДАЛЬШЕ — ПЛАН НА 90 ДНЕЙ

▎НЕДЕЛЯ 1-2: БЫСТРЫЕ ПОБЕДЫ (quick wins)
То, что можно сделать прямо сейчас, без бюджета, силами клиники:

1. [Конкретное действие] — эффект: [цифра из data.json]
   Пример: «Добавить VIP Clinic в bio всех врачей (5 аккаунтов) —
           их 68K подписчиков узнают, где они работают. 0 ₽, 1 час.»
2. [Конкретное действие]
3. [Конкретное действие]

▎МЕСЯЦ 1: ЗАПУСК КОНТЕНТ-МАШИНЫ
Запуск контент-плана из Phase 7:

1. Неделя 1-2: [3 темы из супер-тем, врачи, каналы]
2. Неделя 3-4: [3 темы]
3. Параллельно: GEO-разметка сайта (Medical Schema, FAQPage) —
   [срок] дней, эффект: видимость в ChatGPT/Perplexity

▎МЕСЯЦ 2-3: ЭКСПАНСИЯ И СИСТЕМА
Выход за пределы Instagram, систематизация:

1. Telegram: запуск регулярного контента (сейчас 100-230 просмотров →
   цель 1K+). Формат: [из Phase 7]
2. Дзен: запуск канала — [N] статей/мес, SEO-трафик
3. YouTube: [N] видео/мес из контент-плана
4. Конкурентная разведка: ежемесячный мониторинг [топ-3 конкурентов]
   по методике Phase 4

▎КВАРТАЛ: СТРАТЕГИЧЕСКИЕ ЦЕЛИ
Куда придём через 90 дней:

- DPI: с [текущий] до [целевой] / 100
- IG клиники: с [текущий] до [целевой] подписчиков
- Telegram: с [текущий] до [целевой] просмотров
- Врачи с соцсетями: с [текущий] до [целевой] из [всего]
- Новые пациенты из AI-поиска: [оценка]

Бюджет: [оценка из Phase 3.6 — PR + контент + GEO]
Срок: 90 дней
Следующая контрольная точка: [дата через 30 дней]
```

**Правила составления:**
1. Каждый пункт привязан к КОНКРЕТНОЙ цифре из data.json. Не «улучшить Instagram», а «с 7.2K до 15K подписчиков».
2. Quick wins — только то, что реально сделать за 1-2 недели без денег.
3. Сроки — календарные, не «в течение месяца».
4. Бюджет — из Phase 3.6 (SMI Placement Map) или честно: «требуется уточнение».
5. Кросс-чек с конкурентами: если у конкурента уже есть то, что мы планируем → указать «они уже это делают, нам нужно [превзойти/отличиться]».

**Hard Gate: action plan отправляется вместе с файлом и summary. ОДНОЙ пачкой. Без паузы. Без вопроса «нужно ли?».**

**Hard Gate: ни одного косяка клиента в «На что обратили внимание» — только конкуренты.**
---
Забирайте полный отчёт 📄

1. 37 врачей в штате — огромный потенциал
2. Соцсети только у 2 — остальное поле для роста
3. Конкуренты на той же улице, но без системного подхода
4. На ProDoctorov рейтинг ниже Яндекс Карт — разрыв 2.4 балла
5. GEO-разметка сайта отсутствует — это бесплатный трафик
6. Ваш топ-конкурент @nickor_clinic тратит на рекламу в 2 раза больше, но их сайт грузится 8 секунд
7. У @medskidka врачи не упоминают клинику в соцсетях — их 30K подписчиков не конвертируются

На что обратили внимание: конкуренты сливают бюджет на рекламу без GEO (их сайты не индексируются AI-поиском), а их врачи не привязаны к бренду клиники. Это ваше преимущество — у вас уже есть репутация, осталось её правильно упаковать.
---

**Hard Gate: файл + summary отправляются вместе, одной пачкой, без паузы.**
**Hard Gate: ни одного косяка клиента в «На что обратили внимание» — только конкуренты.**

---

## Post-Mortem: Детство Плюс (июнь 2026)

| Урок | Что было | Теперь |
|------|----------|--------|
| IG клиники верифицировать | @detstvo.plus из старого скрапа - удалён | verify-social-accounts.py |
| IG конкурентов проверять | @aksis_clinic не существует | verify-social-accounts.py |
| Конкурентов системно | 3-4 "из головы", пропущено 13+ | find-competitors.py |
| Каждую цифру в 2+ | Без верификации | 6 проверок перед отправкой |
| Контент-анализ не опция | Пропущен | Phase 3 обязательна |
| Старые данные не использовать | Из памяти | Свежий скрап перед HTML |

## Post-Mortem: VIP Clinic Fake Competitors (июнь 2026)

| Урок | Что было | Теперь |
|------|----------|--------|
| Конкурентов проверять через DocDoc | 5 из 5 конкурентов выдуманы из web_search (не подтверждены) | Competitor Source Gate: каждый конкурент через DocDoc/ProDoctorov/Яндекс.Карты |
| ИНН верифицировать | Предоставленные ИНН (7725353125 и др.) не найдены в EGRUL | Перед EGRUL — подтвердить юрлицо через 2+ источника |
| Proximity Sweep обязателен | Пропущен шаг 2 (соседи по бульвару) | Proximity Sweep — обязательный шаг после ProDoctorov |

## Post-Mortem: ARclinic (июнь 2026)

| Урок | Что было | Теперь |
|------|----------|--------|
| Загружать скиллы при входе | Новая сессия - чистый лист | PRE-FLIGHT Phase 0 (Hard Gate) |
| Не лезть MTProto в чат клиента | Вступил через Людмилу | ЗАПРЕЩЕНО. Только бот |
| SOCKS5 туннель | Активен | Остановлен и отключён |
| **Дрифт контекста** | **Обсуждали дизайн → начал клиента без перезагрузки скилла** | **Iron Rule #2 (PRE-FLIGHT + DRIFT PROTECTION) и response-style: перезагружать скилл после дрифта** |

**См. также:**
- `references/arclinic-drift-autopsy.md` — root-cause анализ дрифта контекста
- `references/arclinic-onboarding-case.md` — полный кейс ARclinic (120.6M выручки, 7 платформ, 5 врачей, топ-6 конкурентов)

## Post-Mortem: Systematic QC Gaps in Three KPs (июнь 2026)

**Reference:** `references/presale-onboarding-gap-map.md` — полная карта соответствия и различий между presale-pipeline и client-onboarding-pipeline.

QC-аудит трёх КП (TORI, ИПХиК, Академия Хрусталёвой) — все прошли только 38-57% QC-чека. **Системные дыры — повторяются во всех трёх, независимо от клиента:**

| Дыра | % КП с проблемой | Причина |
|------|------------------|---------|
| Tech Audit (Фаза 1) | 100% | Полностью отсутствует. Нет PageSpeed, schema, SEO, mobile, alt, sitemap |
| SMI без URL | 100% | Есть упоминания «РБК», «Forbes» — но ни одной прямой ссылки на статью |
| Форумы (Фаза 5) | 100% | Woman.ru, IRecommend, Pikabu — не собраны ни в одном |
| Контент-форматы | 100% | Есть темы врачей, но нет выделения форматов-победителей (шоу/интрига/авторская/школа) |
| Content Plan (Фаза 7) | 67% | Только 1 из 3 КП имеет контент-план |
| QC6 (все соцсети) | 100% | Ни один не содержит IG+TG+VK+YouTube вместе |

**Профилактика:**
1. PRE-BUILD CHECKLIST (Phase 8) — расширен до 11 проверок
2. После Phase 3 (Content Analysis) — обязательная проверка: data.json содержит `content_analysis` с темами/форматами/топ-постом каждого ключевого врача
3. После Phase 3.5 (SMI) — обязательная проверка: каждая статья имеет `url`, а не только `source`
4. После Phase 5 (Forum Pains) — проверка: data.json содержит `forum_pains` с топ-15 болей
5. QC6 проверка: соцсети клиники проверены на ВСЕХ площадках (IG, TG, VK, YouTube, Дзен)
6. Content Plan (Phase 7) — ОБЯЗАТЕЛЕН, не опционально

**Reference:** Полный отчёт аудита с цифрами — `references/qc-audit-three-kps-2026-06.md`

**Reference (методология оценки скиллов):** `references/skill-audit-methodology.md` — 26 блоков × 15 глубинных измерений для оценки SKILL.md против эталонных КП. Использовать при появлении нового эталонного документа или после значительных изменений скилла.

---


## Version History

Подробный список изменений: `references/CHANGELOG.md`



---

## Implementation Notes

Детали реализации правил. Вынесены из декларативных Iron Rules для ясности.

### GOAL LOOP (Iron Rule #9) — алгоритм

```
while gaps > 0 and iterations < 3:
    вернуться к Phase 2-5 для незакрытых gaps
    if новых данных == 0: break
```

- Stopping condition: gaps = 0 ИЛИ 3 полных цикла без новых данных
- Перед HTML: честно указать оставшиеся gaps в секции «Допущения и ограничения»
- gaps отслеживаются в data.json: поле `data.gaps` — массив строк

### PRE-FLIGHT + DRIFT PROTECTION (Iron Rule #2) — алгоритм

Проверка при КАЖДОМ переходе в режим клиента:

```python
if появился_сигнал_клиента(сообщение):
    if контекст_загрязнён():
        skill_view('client-onboarding-pipeline')
        # проверить Phase 0: 5 скиллов загружены?
        # если нет → загрузить
```

### MODEL ROUTING (Iron Rule #8) — HTML на Flash разрешён

```bash
current_model=$(hermes config show 2>&1 | grep -A5 "Model:" | grep "model:" | head -1 | sed "s/.*'model': '//" | sed "s/'.*//")
hermes config set model "deepseek/deepseek-v4-pro"
# ... генерация HTML ...
hermes config set model "$current_model"
```

Если `current_model` уже Pro — не переключать.
Если переключение не удалось — продолжить на Flash. Использовать шаблон client-kp-template.html.

### BOUNDARY SWITCH — сигналы входа в режим клиента

1. Сообщение содержит URL сайта клиники
2. «добавил тебя в чат», «начинай с [клиент]», «это [имя], владелец [клиника]»
3. Название клиники + вопрос про услуги/анализ
4. «онбординг», «presale», «сделай КП», «изучи сайт», «сделай аудит»
5. Упоминание @ (добавление в групповой чат) или контекст группового чата
