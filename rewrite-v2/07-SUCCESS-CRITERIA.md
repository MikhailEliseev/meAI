# 07 — КРИТЕРИИ УСПЕХА

**Дата:** 1 июля 2026
**Статус:** Контракт приёмки MVP
**Принимающая сторона:** Михаил Елисеев

---

## 🎯 ГЛАВНЫЙ КРИТЕРИЙ (ОДНОЙ ФРАЗОЙ)

**Михаил открывает `https://iamaim.ru`, вбивает URL любой коммерческой медицинской клиники → через 5-8 минут открывает готовый отчёт → выглядит так же красиво, как `design-showcase-dual-theme.html`.**

**Stop criterion Михаила:**
> "Мне хочется на простых результатах хотя бы что-то прощупать. Я скажу: да, окей, наконец-то мы хоть что-то получили, пока мы не получили вообще ничего."

**MVP = "хоть что-то получили" = рабочий end-to-end.**

---

## ✅ ОБЯЗАТЕЛЬНЫЕ КРИТЕРИИ (MVP gate)

Все 10 пунктов должны быть выполнены. Если хотя бы один не выполнен — MVP НЕ достигнут.

### Критерий 1: End-to-end pipeline работает

- [ ] Клиент пишет URL в чат на `https://iamaim.ru`
- [ ] Hermes отвечает приветствием или сразу запускает pipeline
- [ ] `run_full_scout` вызывается (видно в логах и через tool_progress SSE)
- [ ] Все 13 фаз выполняются (статус completed или no_data)
- [ ] Через 5-8 минут клиент получает ссылку на отчёт
- [ ] Ссылка формата `https://iamaim.ru/{8-char-slug}`

**Проверка:**
```bash
# Логи
docker logs aim-hermes --tail 100 | grep "Phase"
# должно быть 13 lines "Phase X completed"

# SSE
curl -N -X POST https://iamaim.ru/api/chat/stream \
  -H "Authorization: Bearer $HERMES_API_KEY" \
  -d '{"message":"https://example.ru","session_id":"test"}'
# должно показать 13 phase progress events
```

### Критерий 2: Отчёт публикуется на сайте

- [ ] После завершения pipeline в `wp_posts` появляется новая запись
- [ ] `post_type = 'page'`
- [ ] `post_status = 'publish'`
- [ ] `post_name = 8-символьный slug` (например, `gkzrghmz`)
- [ ] `post_content` начинается с `<!DOCTYPE html>` и заканчивается `</html>`
- [ ] URL `https://iamaim.ru/{slug}` возвращает HTML (не 404, не escaped code)

**Проверка:**
```bash
# Прямой SQL
docker exec aim-mysql mysql -u wp_user -p$WP_DB_PASSWORD wordpress \
  -e "SELECT ID, post_name, post_status, LEFT(post_content, 50) FROM wp_posts
      WHERE post_name REGEXP '^[a-z0-9]{8}$' ORDER BY ID DESC LIMIT 5"

# HTTP
curl -s -o /dev/null -w "%{http_code}" https://iamaim.ru/{slug}
# должно быть 200
```

### Критерий 3: Отчёт отображается в canonical дизайне

- [ ] HTML открывается как красивая страница (не как код)
- [ ] Применена двойная дизайн-система (light + dark)
- [ ] Theme toggle работает (клик → тема меняется, сохраняется в localStorage)
- [ ] Шрифты: Playfair Display + **Jost** (НЕ Inter, НЕ Montserrat)
- [ ] Glass cards видны (с blur эффектом)
- [ ] Анимации работают (card-breathe, glass-glow)
- [ ] Water ripple rings отображаются в light теме
- [ ] Бейджи (metric-tag-green/red/yellow/blue/gray) присутствуют
- [ ] Surface-block-green / surface-block-red присутствуют
- [ ] CTA box в конце отчёта

**Проверка (визуальная):**
1. Открыть URL в Chrome
2. Toggle тема — обе выглядят красиво
3. DevTools → Elements → найти все canonical классы
4. Lighthouse audit: 90+ на Performance, Accessibility, Best Practices

### Критерий 4: Отчёт standalone (без шапки WordPress)

- [ ] На странице НЕТ WordPress header
- [ ] НЕТ WordPress footer
- [ ] НЕТ WordPress admin bar
- [ ] НЕТ WordPress menu
- [ ] НЕТ других элементов темы

**Проверка:**
```bash
curl -s https://iamaim.ru/{slug} | grep -E "(wp-header|footer|admin-bar)"
# должно быть пусто
```

### Критерий 5: Финальные 3 сообщения Hermes

- [ ] После завершения pipeline Hermes отправляет РОВНО 3 сообщения
- [ ] Сообщение 1: КОНТРАСТ (один сильный факт-шок + противоположность)
- [ ] Сообщение 2: ТОЧКИ РОСТА (3 пункта с конкретными действиями)
- [ ] Сообщение 3: ОТЧЁТ (ссылка + описание секций + soft handoff)
- [ ] Тон: эксперт-аналитик (НЕ продавец)
- [ ] НЕТ запрещённых слов: "пресейл", "КП", "купить", "заказать", "прайс"
- [ ] Длина: 1 ≤ 500 символов, 2 ≤ 600 символов, 3 ≤ 400 символов

**Проверка:**
- Прочитать лог чата
- Подсчитать сообщения от Hermes после `run_full_scout`
- Проверить prohibited words: `grep -iE "(пресейл|КП|купить|заказать)" messages.log`

### Критерий 6: Приватность

- [ ] `meta name="robots" content="noindex, nofollow"` в scout-постах
- [ ] Scout-посты НЕ в `sitemap.xml`
- [ ] REST API `wp-json/wp/v2/pages/{id}` возвращает 403 для scout-постов
- [ ] Старые named URLs (av-clinic-*, nachado-*, и т.д.) редиректят 301 на главную
- [ ] Fragment posts (8-char slug без DOCTYPE) в статусе draft

**Проверка:**
```bash
# Sitemap
curl -s https://iamaim.ru/wp-sitemap.xml | grep "{8-char-slug}"
# должно быть пусто

# REST API
curl -s -o /dev/null -w "%{http_code}" \
  -H "Accept: application/json" \
  https://iamaim.ru/wp-json/wp/v2/pages?slug={8-char-slug}
# должно быть 403 (или 401)

# Redirect
curl -s -o /dev/null -w "%{http_code}" https://iamaim.ru/av-clinic-test
# должно быть 301
```

### Критерий 7: Время pipeline

- [ ] На example.ru: ≤ 4 минуты
- [ ] На реальной клинике (diamond-clinic.ru): ≤ 8 минут
- [ ] На любой коммерческой клинике: ≤ 10 минут
- [ ] Если > 10 минут — пользователь получает уведомление "продолжаю в фоне"

**Проверка:**
```bash
# Замерить время
time curl -X POST https://iamaim.ru/api/chat \
  -H "Authorization: Bearer $HERMES_API_KEY" \
  -d '{"message":"https://example.ru","session_id":"test"}'
```

### Критерий 8: Производительность

- [ ] TTFB (time to first byte) < 300ms для scout-постов
- [ ] Lighthouse Performance score ≥ 85
- [ ] LCP (Largest Contentful Paint) < 2.5s
- [ ] CLS (Cumulative Layout Shift) < 0.1
- [ ] FID (First Input Delay) < 100ms

**Проверка:**
- Chrome DevTools → Lighthouse → Run audit на scout-посте

### Критерий 9: Responsive

- [ ] Mobile (375px / iPhone SE): все секции видны, текст читаем
- [ ] Tablet (768px / iPad): адаптивная сетка
- [ ] Desktop (1920px): centrированный контент, max-width 860px
- [ ] Print (Cmd+P): без анимаций, без glass effect, чистый ч/б

**Проверка:**
- Chrome DevTools → Device Toolbar → проверить 3 размера
- Открыть print preview (Cmd+P)

### Критерий 10: Браузерная совместимость

- [ ] Chrome 120+ — всё работает
- [ ] Safari 17+ — всё работает (особенно backdrop-filter)
- [ ] Firefox 120+ — всё работает (backdrop-filter может отличаться)
- [ ] Edge 120+ — всё работает (на Chromium)

**Проверка:**
- Открыть scout-пост в 4 браузерах
- Toggle тема в каждом
- Проверить glass effect в каждом

---

## 🎯 ПРОИЗВОДИТЕЛЬНЫЕ КРИТЕРИИ (post-MVP)

Это НЕ блокирует MVP, но важно для долгосрочного успеха.

### 1. Conversion metrics

- [ ] 30% уникальных посетителей открывают чат
- [ ] 70% открыли чат → отправили URL
- [ ] 95% начали pipeline → завершили
- [ ] 80% получили ссылку → открыли отчёт
- [ ] 10% прошли отчёт → связались с Михаилом

### 2. Стабильность

- [ ] 100 consecutive pipeline прогонов без критического бага
- [ ] 99.5% uptime за неделю
- [ ] 0 потерь данных сессий
- [ ] 0 утечек приватности (sitemap, REST API, redirects)

### 3. Масштабируемость

- [ ] 5 одновременных пользователей без деградации
- [ ] 20 отчётов в день без перегрузки
- [ ] 100 отчётов в день — auto-scale redis cache

### 4. Supportability

- [ ] Логи понятные (INFO для нормальных операций, ERROR для багов)
- [ ] Grafana dashboard показывает метрики pipeline
- [ ] Alertmanager настроен на критические события
- [ ] Документация актуальна

---

## ❌ АНТИ-КРИТЕРИИ (что НЕ должно произойти)

Если ЛЮБОЙ из этих пунктов происходит — проект провален.

1. ❌ Клиент видит экранированный HTML код вместо красивой страницы
2. ❌ Клиент получает отчёт со словом "пресейл", "КП", "купить"
3. ❌ Отчёт попал в sitemap.xml или индексируется Google
4. ❌ REST API отдаёт scout-посты публично
5. ❌ Pipeline занимает > 15 минут
6. ❌ Hermes отправляет 5+ финальных сообщений вместо 3
7. ❌ Шрифт Inter (вместо canonical Jost) в scout-постах
8. ❌ Шапка WordPress на scout-страницах
9. ❌ Theme toggle не работает (или тема не сохраняется)
10. ❌ Государственная клиника не отфильтрована
11. ❌ Дубликат meai framework или других компонентов
12. ❌ Магистры или субагенты упомянуты в SOUL.md
13. ❌ "Я Operator" или "AI-операционный директор" в приветствии
14. ❌ Hermes ломается посреди pipeline без восстановления

---

## 🎬 СЦЕНАРИЙ ПРИЁМКИ (для финального demo)

Михаил и разработчик вместе выполняют:

### Шаг 1: Открытие
- [ ] Михаил открывает `https://iamaim.ru` в Chrome
- [ ] Видит лендинг (light или dark theme — toggle в углу)
- [ ] Лендинг загружается < 2s

### Шаг 2: Чат
- [ ] Михаил кликает "Разобрать мою клинику"
- [ ] Открывается чат (или inline bubble, или full-page)
- [ ] Hermes приветствует (3 предложения, без "Operator")

### Шаг 3: URL
- [ ] Михаил вводит: `https://diamond-clinic.ru`
- [ ] Hermes отвечает: "Запускаю разбор вашей клиники. Это займёт ~6-8 минут."
- [ ] Появляется прогресс-бар с 13 фазами

### Шаг 4: Pipeline
- [ ] Михаил наблюдает прогресс в реальном времени
- [ ] Фазы завершаются по очереди (✅ marks появляются)
- [ ] Whisper-комментарии: 2-3 коротких сообщения от Hermes
- [ ] Через ~7 минут прогресс-бар заполняется

### Шаг 5: Финал
- [ ] Hermes отправляет ровно 3 сообщения
- [ ] Сообщение 1: конкретный контраст с цифрами
- [ ] Сообщение 2: 3 точки роста с действиями
- [ ] Сообщение 3: ссылка на отчёт + soft handoff
- [ ] Михаил НЕ видит слова "пресейл", "купить", "КП"

### Шаг 6: Отчёт
- [ ] Михаил кликает ссылку `https://iamaim.ru/{8-char-slug}`
- [ ] Открывается красивая страница (dark theme by default)
- [ ] Без шапки сайта, без footer
- [ ] Theme toggle работает (sun/moon в правом верхнем)
- [ ] Михаил переключает на light — выглядит так же красиво

### Шаг 7: Содержание
- [ ] Скроллит вниз, видит 10 секций
- [ ] Бейджи с цветными dot (green/red/yellow/blue/gray)
- [ ] Glass cards с blur эффектом
- [ ] Surface blocks (green для сильных, red для слабых)
- [ ] Glass tables для сравнений
- [ ] CTA в конце: "Хотите углубить разбор?"

### Шаг 8: Технические проверки
- [ ] Михаил открывает DevTools → Network → reload
- [ ] TTFB < 300ms
- [ ] Lighthouse audit: 90+
- [ ] Console: 0 errors, 0 warnings
- [ ] View Source: HTML начинается с `<!DOCTYPE html>`

### Шаг 9: Mobile
- [ ] Михаил открывает тот же URL на iPhone
- [ ] Адаптивный дизайн работает
- [ ] Все секции читаемы
- [ ] Toggle работает

### Шаг 10: Приватность
- [ ] Михаил проверяет `https://iamaim.ru/wp-sitemap.xml` — slug НЕТ
- [ ] Михаил проверяет `https://iamaim.ru/wp-json/wp/v2/pages?slug={slug}` — 403
- [ ] Michael checks `view-source:` — `noindex, nofollow` meta присутствует

### Финал: принятие

**Михаил говорит:**
> "Да, окей, наконец-то мы хоть что-то получили."

**MVP достигнут.** 🎉

---

## 📊 ДОКУМЕНТАЦИЯ И РЕПОРТИНГ

### Что фиксируется после MVP

- [ ] RECORD.md — запись успешного прогона (URL, timing, screenshots)
- [ ] BUGS-RESOLVED.md — список багов исправленных во время разработки
- [ ] IMPROVEMENTS-BACKLOG.md — что можно улучшить в v2.1
- [ ] DEPLOY-RUNBOOK.md — инструкция по деплою для будущего разработчика

### Метрики для отслеживания (после MVP)

Еженедельно:
- Количество pipeline прогонов
- Среднее время pipeline
- Conversion rate (URL → отчёт → contact)
- Топ-5 ошибок в логах

Ежемесячно:
- NPS (если внедрить)
- Cost per pipeline run (токены DeepSeek + Apify + Firecrawl)
- Список пользовательских жалоб/предложений

---

## 🚨 ЕСЛИ MVP НЕ ДОСТИГНУТ

### Эскалация

Если хотя бы 1 из 10 обязательных критериев не выполнен:

1. **Не сообщать Михаилу "всё готово"** (это 11-й раз за 2 месяца)
2. **Зафиксировать что именно не работает** (с-specific ошибкой)
3. **Предложить конкретный план фикса** (с временем)
4. **Получить добро Михаила на план**
5. **Реализовать фикс**
6. **Повторить приёмку**

### Принцип

> "Михаил уже слышал 'всё готово' 10+ раз за 2 месяца. Каждый раз либо не работало, либо ломало другое."

**Лучше честно сказать "не работает X, нужно ещё Y дней"** чем "всё готово" и потом объяснять почему отчёт пустой.

---

## 📋 ФИНАЛЬНЫЙ ЧЕК-ЛИСТ (перед объявлением MVP)

Для разработчика:

- [ ] Все 10 обязательных критериев выполнены
- [ ] Smoke test на 5 разных URL пройден
- [ ] Lighthouse ≥ 90 на всех scout-постах
- [ ] 0 критических багов в логах за последние 24h
- [ ] Бэкап сервера актуален
- [ ] Документация обновлена
- [ ] SESSION.md и .current-task актуальны
- [ ] Михаил провёл приёмочный сценарий

Для Михаила:

- [ ] Увидел рабочий end-to-end pipeline
- [ ] Получил красивый отчёт по URL
- [ ] Не нашёл критических проблем
- [ ] Сказал "окей, наконец-то"

---

*Этот документ — контракт приёмки. Любые изменения в критериях требуют обновления этого файла и согласования с Михаилом.*
