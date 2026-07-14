# Phase 5: Кнопки в чате — Summary

**Phase:** 05-buttons-reports
**Completed:** 2026-07-14
**Status:** ✅ Фронтенд готов (CHAT-01..04). Кнопки появятся после переключения на v2 (Phase 6).

## Что сделано

Theme-чат iamaim.ru теперь умеет рендерить кнопки suggestions под ответами ассистента. 4 файла prod-чата обновлены, bundle пересобран и задеплоен в Docker volume.

## Ключевая находка деплоя

Prod-чат — **отдельная кодовая база** в Docker volume `aim_wp_content`, НЕ `wordpress-core/.../assets/js/`. nginx (контейнер aim-nginx) обслуживает bundle из volume `/var/lib/docker/volumes/aim_wp_content/_data/`. Деплой = копирование в volume, не в wordpress-core.

## Файлы (prod-chat, синхронизированы в AIM/prod-chat-backup/)
- `useStreamChat.js` — +case 'suggestions' → buttons в сообщении
- `ChatBubble.jsx` — +чипы `.chat-suggestion-chip` под контентом, onClick → sendMessage
- `chat.css` — +стили чипов (ghost-стиль, var(--accent)/var(--bg))
- `index.jsx` — +buttons/onSuggestionClick в ChatBubble

## Что осталось
- **Phase 6**: переключить prod-чат с aim-hermes → aim-hermes-v2 → кнопки оживут у клиентов
- generate_html_report (отчёты) — Wave 2

*Phase 05 — frontend complete, pending Phase 6 activation*
