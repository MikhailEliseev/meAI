# 21 — ВТОРАЯ НЕЗАВИСИМАЯ ПРОВЕРКА (с нуля, без доверия)

**Дата:** 30 июня 2026, 22:00 UTC
**Подход:** 21 новый тест (NC1-NC21), игнорируя предыдущие выводы
**Принцип:** Каждое предположение = прямой тест

---

# 📊 СВОДКА НОВЫХ ТЕСТОВ

| # | Тест | Результат | Влияние |
|---|---|---|---|
| NC1 | PHP warnings за 24h | Пусто | ✅ Чисто |
| NC2 | PHP-FPM pool config | max_children=5, dynamic | ⚠️ См. ниже |
| NC3 | PHP ini | display_errors=Off, error_log=/dev/stderr | ✅ Хорошо |
| NC4 | Текущая нагрузка WP | 72.55% CPU, 4 процесса | ⚠️ HIGH LOAD! |
| NC5 | Недавно изменённые файлы темы | front-page, footer, theme.css, etc. | ⚠️ Меняется |
| NC6 | OPcache settings | enabled | ✅ Подтверждено |
| NC7 | **OPcache validate_timestamps** | **On, revalidate_freq=2** | ✅ **Можно без restart** |
| NC8 | PHP-FPM master process | sleeping, 1 thread | ✅ Ок |
| NC9 | mu-plugins scout mentions | пусто | ✅ Чисто |
| NC10 | WP_CACHE in wp-config | нет | ✅ Чисто |
| NC11 | object-cache.php / advanced-cache.php | не существуют | ✅ Чисто |
| NC12 | novamira plugin | MCP plugin для Gutenberg | ⚠️ Активен |
| NC13 | .htaccess files | только корневой | ✅ Чисто |
| NC14 | WP cron jobs | novamira_gutenberg_cleanup daily | ✅ Не влияет |
| NC15 | novamira hooks на templates | пусто | ✅ Чисто |
| NC16 | Cron content | стандартные WP cron'ы | ✅ Чисто |
| NC17 | Akismet hooks на templates | пусто | ✅ Чисто |
| NC18 | ?p=ID URLs | 301 редирект | ✅ Корректно |
| NC19 | header.php hooks | wp_head + wp_body_open | ⚠️ Потеряем |
| NC20 | footer.php content | **floating chat button** | 🔴 **ВАЖНО!** |
| NC21 | Footer полный | frost-overlay + chat emerge + floating button | 🔴 **ВАЖНО!** |

---

# 🔴 НОВЫЕ КРИТИЧНЫЕ НАХОДКИ

## NC-HIGH-1: Floating Chat Button потеряется на scout-страницах

**Факт:** Footer.php содержит:
- Floating chat button ("AIM Ассистент") — fixed bottom-right
- Frost overlay для чата
- Chat emerge container
- `wp_footer()` hook

**Если scout отчёт НЕ вызывает get_footer():**
- ❌ Floating chat button НЕ показывается на scout странице
- ❌ Клиент после прочтения отчёта НЕ может сразу начать чат
- ❌ Точка конверсии потеряна

**Вопрос для Михаила:** Это ок? Или нужно сохранить floating chat на scout страницах?

## NC-HIGH-2: wp_head() потеря для scout страниц

**Если НЕ вызывать get_header():**
- ❌ GTM (Google Tag Manager) НЕ загрузится
- ❌ Schema.org JSON-LD НЕ будет
- ❌ WordPress SEO meta НЕ будут
- ❌ Preconnect для шрифтов НЕ загрузится

**Реальное влияние:** Аналитика не посчитает показы scout отчётов.

**Вопрос:** Это acceptable? Или нужна аналитика?

## NC-MED-1: PHP-FPM load 72% CPU на одном контейнере

**Снимок:** `aim-wordpress` сейчас использует 72.55% CPU.

**Риск:** Если во время deploy нагрузка растёт → PHP-FPM pool исчерпан → 502 Bad Gateway.

**Митигация:** Deploy в окно минимальной нагрузки (ночь MSK). Или кратковременно (5 секунд).

## NC-MED-2: Текущая активность — файлы меняются

**Факт:** 10 файлов темы недавно изменены:
- front-page.php
- footer.php
- chat-inline.php
- aim-pro-endpoints.php
- assets/js/chat-bundle.js + css
- theme.css
- и т.д.

**Вопрос:** Кто-то сейчас редактирует? Или это недавний deploy?

**Митигация:** Проверить, не идёт ли работа. Если да — НЕ деплоить сейчас.

---

# 🎯 ОБНОВЛЁННЫЕ РИСКИ (с новыми находками)

## 🔴 КРИТИЧНЫЕ

1. **Floating chat потеряется** — Михаил может не хотеть этого
2. **Аналитика (GTM) не загрузится** — Михаил может хотеть трекинг scout просмотров

## 🟡 СРЕДНИЕ

3. **PHP-FPM load 72%** — небольшое окно риска во время deploy
4. **Недавние изменения файлов** — нужно подтвердить что никто не работает

## 🟢 ОЖИДАЕМЫЕ (которые мы знаем)

5. **17 из 72 scout постов починятся**, 55 останутся (фрагменты)
6. **index.php change atomic** через OPcache (revalidate_freq=2)

---

# 🚨 ВОПРОСЫ ДЛЯ МИХАИЛА (перед "go")

Эти вопросы **новые**, не освещены в предыдущих итерациях:

### Вопрос A: Floating Chat Button на scout-страницах

**Сценарий:** Клиент открывает `iamaim.ru/gkzrghmz` — видит красивый отчёт. Дочитывает. Хочет задать вопрос.

**Текущий план:** Floating chat НЕ показывается (мы НЕ вызываем get_footer).

**Альтернативы:**

**A1.** Оставить как в плане — chat НЕ показывается на scout-страницах.
   - Pros: Чистый HTML отчёта, без distractions
   - Cons: Клиент должен вернуться на главную для чата

**A2.** Добавить floating chat button в HTML template отчёта.
   - Pros: Клиент может сразу начать чат
   - Cons: Нужно менять `generate_html_report.py` (Python код)

**A3.** Минимальный inline JS в scout-report-template.php для показа chat после отчёта.
   - Pros: Без изменения Python, но с chat
   - Cons: Сложнее template

### Вопрос B: Аналитика (GTM) на scout-страницах

**Сценарий:** Хочет ли Михаил видеть в GTM сколько людей открыли scout отчёты?

**B1.** Да — добавить GTM snippet в scout-report-template.php
**B2.** Нет — оставить как есть (HTML без GTM)

### Вопрос C: Время deploy

Сейчас `aim-wordpress` на 72% CPU.

**C1.** Подождать до ночи MSK (минимальная нагрузка)
**C2.** Деплоить сейчас, быстро (< 30 секунд)
**C3.** Проверить никто ли не работает на сервере сейчас

---

# 🎯 УЛУЧШЕННЫЙ КОД (с GTM опционально)

```php
<?php
/**
 * Fallback template.
 *
 * Scout reports (8-char slug + full HTML document) выводятся raw HTML.
 * Остальное — стандартный theme wrapping.
 */
$post = get_queried_object();

$is_scout_report = (
    is_page()
    && !is_admin()
    && !is_search()
    && !is_archive()
    && $post instanceof WP_Post
    && empty($post->post_password)
    && preg_match('/^[a-z0-9]{8}$/', $post->post_name)
    && strpos($post->post_content, '<!DOCTYPE html>') === 0
    && strpos($post->post_content, '</html>') !== false
);

if ($is_scout_report) {
    // Raw HTML output
    header('Content-Type: text/html; charset=utf-8');
    header('Cache-Control: no-store, no-cache, must-revalidate');
    header('Content-Length: ' . strlen($post->post_content));
    echo $post->post_content;
    exit;
}

// Default WP theme-wrapped output
get_header();
if (have_posts()) {
    while (have_posts()) {
        the_post();
        the_content();
    }
}
get_footer();
```

**Изменения:**
- ✅ strlen (bytes) — правильно для Content-Length
- ✅ is_page() + !is_search() + !is_archive() — narrow scope
- ✅ 8 слоёв защиты
- ✅ Comments для понимания

**Что НЕ делает (после твоего решения):**
- ❌ Floating chat button (если хочешь — нужно отдельно)
- ❌ GTM analytics (если хочешь — нужно отдельно)

---

# 📋 ОБНОВЛЁННЫЙ ПЛАН (с новыми находками)

## Перед deploy: подтвердить с Михаилом

1. **Floating chat на scout страницах:** A1 (не показывать) / A2 (Python change) / A3 (JS inject)?
2. **GTM на scout страницах:** B1 (да) / B2 (нет)?
3. **Время deploy:** C1 (ждать ночь) / C2 (сейчас) / C3 (проверить активность)?

## После подтверждения

1. Backup index.php (1 мин)
2. Создать новый index.php (5 мин)
3. PHP syntax check (2 мин)
4. Deploy через docker cp (2 мин)
5. 11 smoke tests (10 мин)
6. Rollback готов (1 мин)

## Smoke tests (обновлённые)

1. `curl -sI https://iamaim.ru/` → 200 (главная)
2. `curl -s https://iamaim.ru/gkzrghmz/ | grep -c "<!DOCTYPE"` → 1
3. `curl -s https://iamaim.ru/4lfyyrht/ | grep -c "<!DOCTYPE"` → 1
4. `curl -s https://iamaim.ru/fs3r3h3u/ | grep -c "<!DOCTYPE"` → 1
5. `curl -s https://iamaim.ru/7w3xqcwo/ | grep -c "<!DOCTYPE"` → 1
6. `curl -sI https://iamaim.ru/prices/` → 200
7. `curl -sI https://iamaim.ru/wp-admin/` → 200/3xx
8. `curl -sI "https://iamaim.ru/?s=test"` → 200
9. `curl -sI https://iamaim.ru/nonexistent123` → 404
10. `curl -s https://iamaim.ru/gkzrghmz/ | wc -c` → ~47000 (раньше 80000)
11. `curl -sI https://iamaim.ru/gkzrghmz/` → содержит `Cache-Control: no-store`

---

# 💡 ЧЕСТНЫЙ ОТЧЁТ ПО ВТОРОЙ ПРОВЕРКЕ

## Что я нашёл нового (что пропустил в первой проверке)

1. **Floating chat button потеряется** — не учёл в первой проверке
2. **GTM не загрузится** — не учёл
3. **PHP-FPM 72% CPU** — не проверял load перед deploy
4. **Недавние изменения файлов** — не проверял кто работает

## Вывод

**Прежде чем деплоить — нужно 3 решения от Михаила:**
- Floating chat (A1/A2/A3)
- GTM (B1/B2)
- Время deploy (C1/C2/C3)

---

**Вопрос к тебе:**

Готов ответить на 3 новых вопроса (A, B, C)? Они возникли только после второй независимой проверки. Без ответов — деплой может потерять функционал (floating chat, аналитика).

Или хочешь ещё проверки?
