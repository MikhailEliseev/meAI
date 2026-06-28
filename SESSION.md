# Session: 2026-06-27 — Phase 9 Context Complete

## Текущий фокус

**Ожидание отката сервера на 2 дня назад**

**Что произошло:**
- Phase 09 задеплоена на сервер (27.06 23:18)
- WordPress откачен на версию ДО Phase 09 (25.06)
- Обнаружена потеря HeadroomGuard обёртки (не закоммичена, не забэкаплена)
- Пользователь откатывает весь сервер на 2 дня назад

**Phase 09 полностью сохранена:**
- `~/Desktop/phase09-COMPLETE-20260628-022838.tar.gz` (446 KB)
- Содержит: AIM/hermes/app/, AIM/theme/, SESSION.md, .current-task
- Все файлы верифицированы по MD5

**Новые правила добавлены:**
- ✅ `scripts/auto-commit-deploy.sh` — автокоммит перед деплоем
- ✅ `.git/hooks/pre-push` — автокоммит перед push
- ✅ CLAUDE.md обновлён с правилом Auto-Commit Before Deploy

**После отката сервера:**
1. Восстановить Phase 09 из бэкапа
2. Попытаться найти HeadroomGuard в серверных бэкапах (20-27 июня)
3. Если нет — интегрировать заново из https://github.com/headroomlabs-ai/headroom.git

---

## Что сделано за сессию (2026-06-27)

### Phase 9: Chat Pro — Website Chat UX Overhaul

**Статус:** Context gathering complete, ready for planning

**35 решений зафиксировано:**
- **D-01 to D-06:** Telegram-style floating progress status (одно сообщение обновляется)
- **D-07 to D-13:** LLM wow-commentary после каждого инструмента с бизнес-языком
- **D-14 to D-20:** Canonical template approach для фикса generate_html_report.py
- **D-21 to D-27:** Нативный диалоговый сбор контактов (не формы)
- **D-28 to D-34:** Services sales assistant с semantic matching
- **D-35:** 4 плана реализации

**10 канонических референсов:**
1. design-showcase-dual-theme.html — единственный канон дизайна
2. theme.css — CSS variables
3. hermes-chat.html — текущий чат (нужно переработать SSE handling)
4. main.py — SSE streaming, push_tool_progress()
5. agent_wrapper.py — AIAgent lifecycle
6. agent_wrapper_optimized.py — mode prompts
7. collect_contact.py — существующий tool
8. generate_html_report.py — сломан, нужен фикс
9. ИПХиК (2).html — референс отчёта (10 секций, 965 строк)
10. services.md — catalogue AIM услуг (создать если отсутствует)

**6 идей отложено в backlog:**
- A/B тестирование UX
- Multi-language поддержка
- Voice input в web chat
- Real-time preview отчёта
- Nише-специфичные шаблоны
- CRM интеграция

---

## Предыдущая сессия (2026-06-26)

### Plan A++ закрыт (13 коммитов)
- 33 AIM tools + 16 debug = 51 всего
- HTML отчёты 42-49KB стабильно
- glm-5 через z.ai Coding Plan
- Backup: `/opt/backups/plan-a-plus-plus-final-20260625-224113.tar.gz`

### Chat PRO добавлен (1 коммит + fix)
- Phase tracker (8 фаз пресейла)
- Live counters (конкуренты, отзывы, врачи)
- Report preview card с WOW reveal анимацией
- Fallback form для email/telegram
- Endpoint `/wp-json/aim/v1/fallback` — тест прошёл

### Auto-URL extraction в run_prescan
LLM иногда забывает передать URL (особенно glm-5). Добавлен fallback: если URL не передан, инструмент сам ищет URL в последних 3 user сообщениях через state.db.

## Backup после всех изменений

**`/opt/backups/hermes-with-chat-pro-20260626-060335.tar.gz`** (146KB, 17 файлов)

Включает:
- Hermes backend (Python)
- SOUL.md (106KB)
- config.yaml
- WordPress (PHP: chat-inline, chat-inline-pro, aim-pro-endpoints, functions)

## Что протестировано

✅ **Backend tests passed:**
- POST /wp-json/aim/v1/fallback (email) → 200 OK
- POST /wp-json/aim/v1/fallback (telegram) → 200 OK
- Homepage 200 OK
- run_prescan auto-URL extraction
- z.ai integration (zai_reader, zai_search, zai_zread)
- Phase tracker / report preview деплой

❌ **Что НЕ удалось протестировать из-за 429:**
- Phase tracker UI в живом пресейле
- Report preview reveal анимация
- Полный end-to-end flow (URL → отчёт → ссылка)

## Текущее состояние production

```yaml
LLM_MODEL: glm-5 (z.ai Coding Plan через OMNIROUTE_URL)
PRESALE iter: 15, tokens: 12000
reasoning_config: {"enabled": False}
SOUL.md: 106KB (12 few-shot сценариев)
AIM tools: 33 зарегистрировано (16 стабильно используются LLM)
Debug tools: 16 (4 мёртвых удалено)

WordPress:
- chat-inline.php (с hook points для pro)
- chat-inline-pro.php (phase tracker + report + fallback)
- aim-pro-endpoints.php (REST endpoints)
- functions.php (include endpoints)
```

## 16 коммитов за сессию

Plan A++ (13):
1. da08350 activate 11 new tools + remove v7
2. 25ca532 auto-pick + PRESALE=15
3. be9d14a rich narrative_md
4. 8737eb9 multi-turn infrastructure
5. bb625d2 review_platforms + instagram_content
6. d7ee17f redundancy philosophy
7. e00e01c scraper optimization
8. 3ca06ea 8 few-shot examples
9. af2edf9 few-shot v2 (crawlee + extract)
10. 8fed791 framework-level multi-turn + JS fallback
11. 942f767 z.ai integration
12. 1f0d8f1 few-shot v3 (zai triggers)
13. 7be2f47 close Plan A++

Chat PRO (2):
14. f94b4a4 chat-pro phase tracker + report preview + fallback
15. 52d7a7c document chat-pro deployment

Auto-URL fix (1):
16. (run_prescan.py auto-URL extraction — deployed но не закоммичен в git separately, в backup включён)

## Deploy state на сервере

```
aim-hermes (healthy):
- /opt/hermes/app/tools/run_prescan.py (auto-URL extraction)
- /opt/hermes/app/tools/zai_tools.py
- /opt/hermes/app/tools/generate_html_report.py (framework quality gate)
- /opt/hermes/app/tools/web_scraper.py (JS auto-fallback)
- /opt/hermes/app/tools/__init__.py (33 tools, 4 dead deregistered)
- /opt/hermes/app/tools/shell_exec.py (file_write append=true)
- /opt/hermes/app/agent_wrapper.py (_mode_limits + auto-pick)
- /opt/data/SOUL.md (106KB)
- /opt/hermes/config.yaml (v3.3 minimal)

aim-wordpress (healthy):
- /var/www/html/wp-content/themes/aim-theme/chat-inline.php (+3 hooks)
- /var/www/html/wp-content/themes/aim-theme/chat-inline-pro.php (NEW)
- /var/www/html/wp-content/themes/aim-theme/aim-pro-endpoints.php (NEW)
- /var/www/html/wp-content/themes/aim-theme/functions.php (+include)
```

## Memory обновлён

- `MEMORY.md` — добавлен указатель на zai-coding-plan-limits.md
- `zai-coding-plan-limits.md` — peak/off-peak часы, стратегия
- `hermes-plan-a-plus-plus.md` — полный референс архитектуры

## Что делать после 13:00 МСК

1. Очистить localStorage в браузере (F12 → Application → Local Storage → iamaim.ru)
2. Открыть iamaim.ru (Ctrl+F5)
3. Отправить URL клиники в чат
4. Наблюдать:
   - Phase tracker (8 фаз) должен появиться
   - Live counters (5 конкурентов, 22 врача и т.д.)
   - Финальный report preview с CTA на https://iamaim.ru/{slug}
   - Если нужно уйти — fallback form

## Deploy constraints

- aim-hermes: НЕ `docker compose up` (затрёт docker cp). Только restart.
- aim-wordpress: можно `docker compose up` (файлы в volume aim_wp_content)
- Backup перед любым изменением: `/opt/backups/...`

## Ключевые архитектурные принципы

1. **LLM = единственный оркестратор** (без Python state machines)
2. **Избыточность = фича** (dedicated + perplexity = cross-validation)
3. **Framework handles correctness** (auto-URL, JS fallback, narrative gate)
4. **Mode-based limits** (PRESALE=15, ADMIN=12, ACTIVE=6)
5. **z.ai Coding Plan exploitation** (бесплатно: LLM, reader, search, zread)

## Что НЕ делать

- ❌ Тестировать в 09:00-13:00 МСК (peak в Китае)
- ❌ Добавлять ещё few-shot в SOUL.md (потолок 100KB достигнут)
- ❌ Возвращать PipelineEngine или state machines
- ❌ Удалять perplexity_search (избыточность = фича)
