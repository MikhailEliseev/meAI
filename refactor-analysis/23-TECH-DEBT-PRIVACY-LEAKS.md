# 23 — ТЕХНИЧЕСКИЙ ДОЛГ: Утечки приватности (FIX LATER)

**Дата:** 1 июля 2026, 06:35 UTC
**Решение Михаила:** Вариант 2 — фикс отображения сейчас, утечки потом
**Статус:** Известные проблемы, НЕ блокируют deploi index.php v2

---

# 🔴 ИЗВЕСТНЫЕ УТЕЧКИ (отдельно от фикса)

## LEAK-1: Sitemap индексация scout постов

**Проблема:** Все 72 scout URLs в публичном sitemap
- URL: `https://iamaim.ru/wp-sitemap-posts-page-1.xml`
- 91 URL включая scout посты
- Google может их проиндексировать

**Фикс (позже):** Отфильтровать scout URLs из sitemap
```php
add_filter('wp_sitemaps_posts_query_args', function($args) {
    $args['post__not_in'] = [/* 72 scout IDs */];
    // Или фильтр по post_name regex
    return $args;
});
```

## LEAK-2: REST API утечка

**Проблема:** `https://iamaim.ru/wp-json/wp/v2/pages?search=AIM+Scout` отдаёт 90 постов публично
- Любой может выкачать все scout отчёты через REST API
- Включая content.rendered = полный HTML

**Фикс (позже):** Запретить REST API для scout постов
```php
add_filter('rest_prepare_page', function($response, $post) {
    if (preg_match('/^[a-z0-9]{8}$/', $post->post_name)
        && strpos($post->post_content, '<!DOCTYPE html>') === 0) {
        // Требовать auth для scout постов
        if (!current_user_can('edit_posts')) {
            return new WP_Error('rest_forbidden', 'Private', ['status' => 403]);
        }
    }
    return $response;
}, 10, 2);
```

## LEAK-3: Named URLs с именами клиник

**Проблема:** Старые scout URLs с именами клиентов в slug:
- `/av-clinic-presale-analysis-3/` ← слово "presale" + имя клиента
- `/nachalo-clinica-analysis-` (×4)
- `/yutskovskaya-analysis/` (×2)
- `/av-clinic-analysis/`

**Имена клиентов в URL видны Google и публично.**

**Фикс (позже):**
1. Удалить эти посты (или поставить draft)
2. Или 301 redirect на главный
3. Или переименовать slug в случайный 8-char

## LEAK-4: OG/Twitter meta tags отсутствуют

**Проблема:** Scout HTML не содержит og:title, og:description, og:image
- Share в Telegram/VK покажет ужасную превью
- Браузер может вытащить первый `<p>` как описание

**Фикс (позже):** Добавить в `_build_report_html()` (Python) OG tags:
```html
<meta property="og:title" content="Анализ клиники {name}">
<meta property="og:description" content="Подробный анализ рынка и точек роста">
<meta property="og:type" content="website">
```

## LEAK-5: x-robots-tag: noindex для REST API, но не для HTML

**Наблюдение:** REST API ответы имеют `x-robots-tag: noindex`, но scout HTML страницы НЕ имеют `noindex`.

**Фикс (позже):** Добавить `<meta name="robots" content="noindex,nofollow">` в scout HTML.

---

# 📋 ПОРЯДОК ФИКСОВ ПОСЛЕ DEPLOI INDEX.PHP

| Приоритет | Утечка | Сложность | Когда |
|-----------|--------|-----------|-------|
| 1 | LEAK-3 (named URLs) | 5 мин | Сразу после фикса отображения |
| 2 | LEAK-1 (sitemap) | 10 мин | В тот же день |
| 3 | LEAK-2 (REST API) | 15 мин | В тот же день |
| 4 | LEAK-4 (OG tags) | 30 мин | На следующей неделе |
| 5 | LEAK-5 (noindex) | 5 мин | С LEAK-4 |

---

# ⚠️ ПРИНЯТЫЙ РИСК

После deploi v2:
- ✅ 17 scout постов будут красиво отображаться
- ❌ Эти 17 постов НЕ защищены от Google indexing
- ❌ REST API остаётся публичным
- ❌ Named URLs остаются видимыми

**Митигация:** Запланировать закрытие утечек в течение 24 часов после deploi.
