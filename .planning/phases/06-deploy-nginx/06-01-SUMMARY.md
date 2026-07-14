# Phase 6: Деплой на прод — Summary

**Phase:** 06-deploy-nginx
**Completed:** 2026-07-14
**Status:** ✅ V2 НА ПРОДЕ — iamaim.ru чат ходит в aim-hermes-v2

---

## Что сделано

Prod-чат iamaim.ru переключён со старого `aim-hermes` на новый `aim-hermes-v2`. Реальные клиенты теперь общаются с новым Гермесом — с tool-calling, базовым сценарием и кнопками suggestions.

## Маршрутизация (как это работает)

```
Клиент (iamaim.ru)
  → Theme-чат (React bundle)
  → /wp-json/aim/v1/chat/stream (WP REST, PHP curl-прокси)
  → HERMES_API_URL = http://aim-hermes-v2:8000/api/chat/stream
  → aim-hermes-v2 (glm-5.2 через Z.AI + 7 тулов)
```

Ключевое: PHP `aim_proxy_chat_stream` — transparent curl-прокси (эхо потока as-is). Формат SSE (`data: {...}\n\n`) совместим между старым hermes и v2.

## Доказательства (evidence, measured)

### E2E 1: «Привет» → ответ (11с)
- 101 text-delta, 1 suggestions, 0 errors, 1 finish
- Ответ: «Я Гермес — AI-ассистент маркетингового агентства AIM...»

### E2E 2: URL → база → кнопки (214с = 3.6 мин)
- 749 text-delta, 2 тулза (quick_overview + find_competitors), 1 suggestions (4 кнопки), 0 реальных ошибок
- База: «СТОМУС, СПб, пр. Луначарского 49, стоматология...»
- Кнопки: Глубокий анализ / СМИ / Отзывы / Соцсети

### Здоровье
- Все 5 контейнеров: aim-app, aim-hermes, aim-hermes-v2, aim-wordpress, aim-nginx — healthy
- Старый aim-hermes жив → откат работает

## Как переключали

`WORDPRESS_CONFIG_EXTRA` в docker-compose: `http://hermes:8000` → `http://aim-hermes-v2:8000`. Затем `docker compose up -d wordpress` (пересоздал контейнер с новым env). Одно изменение.

## Разведка-находки (важно)

1. **wp-config.php (host)** = `hermes-fresh:8000` (устаревшее, НЕ используется — контейнер берёт env из compose)
2. **aim-wordpress env** = переопределяется через `WORDPRESS_CONFIG_EXTRA` (Docker WP official image паттерн)
3. **PHP прокси** = transparent SSE (не парсит JSON), значит формат совместим
4. **Старый hermes** уже эмитил SSE `data:` формат — v2 унаследовал совместимость

## Откат план (<2 минуты)

```bash
ssh aim "cd /opt/aim/AIM"
# вернуть HERMES_API_URL
sed -i "s|aim-hermes-v2:8000|hermes:8000|" docker-compose.yml
docker compose up -d wordpress
# старый aim-hermes жив, сразу подхватится
```

Или из backup: `cp docker-compose.yml.bak-phase6-20260714-181313 docker-compose.yml`

---

## ПРОЕКТ ЗАВЕРШЕН 🎉

Гермес v2 полностью на проде. 6 из 6 фаз выполнены.

*Phase 06 — COMPLETE. Project "Гермес v2" delivered to production.*
