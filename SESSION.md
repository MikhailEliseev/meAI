# Session: 2026-06-17 (продолжение)

## Текущий фокус: Исправление багов 3-фазного пайплайна (завершено)

### Результаты тестовой сессии

**Задеплоено на Polish server:**
- `agent_wrapper.py` — max_iterations=5 для PRESALE (было 25)
- `agent_wrapper.py` — запрет на api_debug и orchestrate в промпте
- `agent_wrapper.py` — NOTE: hermes-debug ОБЯЗАТЕЛЕН (баг #17)
- `quick_overview.py` — REQUEST_TIMEOUT 45s + retry с backoff 2s
- `run_prescan.py` — health check + retry с backoff 5s + явный httpx.Timeout(connect=10, read=600, write=30, pool=10)

### Результат E2E-теста (nachalo-clinica.ru)
- tool_calls: ТОЛЬКО quick_overview + run_prescan (без api_debug и orchestrate!) ✅
- quick_overview: сработал ✅
- run_prescan: 513s (долго, но работает с новым 600s таймаутом) ✅
- Модель вернула реальные данные: ИНН 6164142132, выручка 24.8 млн ₽, рост +49% ✅
- max_iterations=5: модель использовала 4/5 api_calls, finish_reason=stop ✅
- 9 из 17 багов исправлены ✅

### Ключевое открытие: БАГ #17
При `enabled_toolsets = ["aim-operations"]` модель вызывает ВСЕ инструменты БЕЗ параметров.
Workaround: всегда включать `hermes-debug` и запрещать api_debug/orchestrate в промпте.

### Оставшиеся баги (8 штук)
- 🔴 #10: prescan-staged: неверный город (СПб вместо Ростов-на-Дону)
- 🔴 #12: Клиент получает таймаут через 910s (частично исправлен max_iterations=5)
- 🔴 #14: Ответ модели теряется при asyncio timeout
- 🔴 #15: Nginx 600s < Hermes 910s
- 🟡 #1: Тестовые URL устарели
- 🟡 #6: $2-4 за пресейл на Claude (улучшено max_iterations=5 но всё ещё дорого)
- 🟡 #13: rusprofile search 404
- 🟡 #16: WordPress duplicate HERMES_API constants

### TODO (будущие сессии)
- Починить геолокацию в prescan-staged (Баг #10)
- Согласовать таймауты: Nginx ↔ Hermes ↔ prescan-staged
- Переезд на DeepSeek V4 Pro для продакшена
- Telegram-доставка результатов background_pipeline
- Deep Research Phase 0 (plan 28)
