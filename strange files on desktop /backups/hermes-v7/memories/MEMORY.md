Скилл client-onboarding-pipeline v6.2.0 — СОЗДАН 2026-06-19 (вырезан из SOUL.md). Phase 6: pb.nalog.ru→bo.nalog.gov.ru. Таблица конкурентов ВСЕГДА: выручка, прибыль, маржа, тренд, численность, нарушения. Execution Log gate перед HTML: проверять ВСЕ [ ].
§
Дизайн-система AIM — единственный источник стилей для всех отчётов: https://iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html#colors. Категорически запрещено: подбирать стиль под клинику, использовать inline-стили, embedded CSS. Только CSS-классы AIM: .glass, .glass-stat, .glass-panel, .hero-stat, .metric-tag, .badge. UI/UX Pro Max — для контроля качества готового отчёта (контраст, доступность, антипаттерны, анимация), НЕ для выбора дизайна. Проверка UX — предупреждения, не блокирует публикацию.
§
Perplexity MCP: @perplexity-ai/mcp-server, 4 инструмента (ask/research/reason/search). Ключ в config.yaml → mcp_servers.perplexity.env. Скрипт perplexity_search.py удалён. В пайплайне — только MCP-инструменты.
§
Скилл client-onboarding-pipeline: все скрипты внутри `scripts/` скилла. Внешние пути (`/opt/hermes/scripts/`, `/root/bin/`) — легаси, заменять на Perplexity API + browser_navigate. Карта: `references/scripts-map.md`.
§
СТОП-ГATE перед HTML (скилл v6.2.0+): пройти по ВСЕМ фазам 0→7, проверить Execution Log. Хотя бы один пустой [ ] → вернуться и доделать. Контекст-гигиена: загруженный пример старого отчёта НЕ заменяет фазы пайплайна. Данные только из инструментов.
§
.env protected — NO tool write. /opt/data/.env loses LLM keys on restart (only Apify/Firecrawl survive). /opt/hermes/.env keeps OpenRouter+DeepSeek keys. Config auto-reverts at startup to deepseek-reasoner/deepseek provider — something overwrites it. DeepSeek streaming via CloudFront fails (RemoteProtocolError). Model names must be verified — "gpt-5.2-nanosoft" hallucinated. Verify keys in BOTH .env and model in config.yaml after restart.