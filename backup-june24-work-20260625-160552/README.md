# Бекап работы 24-25 июня 2026

## Что включает
- planning-phases-04-07/ — все PLAN.md, SUMMARY.md, VERIFICATION.md Phase 4-7
- hermes-app/ — Python файлы + SOUL.md (оптимизированные версии)
- server-reports/ — HTML отчёты с сервера + reference

## Текущее состояние
- Pipeline работает end-to-end на GLM-5-turbo (z.ai Coding Plan)
- HTML отчёты генерируются через narrative_md → styled HTML
- Оптимизация промптов: -66% токенов (SOUL.md 47K→6K, Pass 3 36K→10K)
- Документация синхронизирована (Phase 6 complete)
- Финальный отчёт iphk.ru: 20.7 KB, 7 секций

## Что НЕ работает
- Coverage < 30% (LLM вызывает 4-5 инструментов вместо 14)
- Нет данных о конкурентах (find_competitors не вызывается)
- Нет финансов (find_company_financials не вызывается)
- Отчёт в 4 раза меньше референса (20 KB vs 78 KB)

## Решение
Откат к v3.3.0 от 7 июня (commit 8b81ae5) — PipelineEngine вместо LLM-оркестратора.
Эта версия валидирована пользователем, генерирует отчёт 78 KB с 10 секциями.
