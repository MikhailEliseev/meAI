# Автономная сессия — Отчёт для Михаила (2026-07-16)

## Что сделано

### 8 багфиксов (детальный план в docs/superpowers/plans/2026-07-16-data-accuracy-bugfixes.md)

| # | Bug | Severity | Fix | Status |
|---|-----|----------|-----|--------|
| 1 | Robots parser: consecutive User-agent overwrite | 🔴 | Accumulate agents, reset on blank line | ✅ |
| 2 | Doctor heading regex matches "Акции"/"Контакты" | 🔴 | Require name+initials pattern | ✅ |
| 3 | Instagram: duplicate Firecrawl search + no private accounts | 🔴 | Removed elif, added private check | ✅ |
| 4 | scraped_services type violation (list[str] vs list[dict]) | 🔴 | New revenue_history field | ✅ |
| 5 | Brand resolver: up to 100s per brand, no timeout | 🔴 | 20s aggregate wait_for + 15s per-request | ✅ |
| 6 | VK followers: "12,345" → 12 (comma=decimal) | 🟡 | Treat comma as thousands separator | ✅ |
| 7 | _is_related_entity: generic words match (Клиника/Центр) | 🟡 | Stopword filter | ✅ |
| 8 | Firecrawl exhausted keys: dead forever | 🟡 | TTL 1 hour | ✅ |

### 5 раундов Code Review

| Round | Found | Fixed |
|-------|-------|-------|
| 1 | 🔴 dead code _count_doctors_on_page | ✅ |
| 2 | 🔴 robots.txt CRLF + wildcard | ✅ |
| 3 | 🔴 robots.txt wildcard false blocked | ✅ |
| 4 | 🟡 brand_resolver timeout mismatch + dead try/except | ✅ |
| 5 | 🔴 orphaned try: (SyntaxError) | ✅ |

### Тесты на двух клиниках

**IPHK (крупная, Москва):**
- GEO: 70, CMS: 1C-Bitrix, VK: 1700, Revenue: 4.1B
- 5 конкурентов: ЛАНЦЕТЪ, Атлас, Рассвет, Seline, Столица
- Все с выручкой, прибылью, трендом, IG

**ARclinic (средняя, СПб):**
- GEO: 70, CMS: 1C-Bitrix, VK: 3200, Telegram: найден, Revenue: 120M
- 5 конкурентов: Мераки, Груздев, Клиника на Невском, МирраМед, Отражение
- Все с выручкой, прибылью, трендом, IG

### Оставшиеся проблемы (для следующей сессии)

1. **ЛАНЦЕТЪ** — дочерняя компания IPHK (разные ИНН/ОГРН). Нужна база корпоративных связей.
2. **Яндекс.Карты рейтинг** — Perplexity не всегда находит (arclinic=None, iphk=None во второй прогонке).
3. **Врачи клиента** — scrape_doctors не находит /specialists для всех сайтов.
4. **SCL** — ФНС не отдаёт sclCount для части компаний.
5. **Время** — pipeline ~60-120с через чат. Нужно оптимизировать.

### Commits за эту сессию: 50+
### Backup: meAI_1-backup-20260716-final + /opt/backups/code-backup-20260716-final/
