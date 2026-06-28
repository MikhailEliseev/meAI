# Session: 2026-06-28 — Phase 09 Deployed

## Текущий фокус

**Phase 09 развёрнут и готов к тестированию**

**Что сделано:**
- ✅ Hermes backend: report_url в finish event (main.py модифицирован, backup создан)
- ✅ WordPress frontend: hermes-chat-pro.html с Phase Tracker (1020 строк)
- ✅ WordPress backend: aim-pro-endpoints.php с fallback REST API (172 строки)
- ✅ functions.php обновлён для подключения endpoints (backup создан)
- ✅ Hermes контейнер перезапущен (04:56:47 UTC)
- ✅ Fallback endpoint протестирован (работает)

**Что добавляет Phase 09:**
1. **Phase Tracker** — 8 фаз пресейла с real-time прогрессом
2. **Report Preview** — WOW-карточка с готовым отчётом + CTA
3. **Fallback Form** — сбор email/telegram для отправки отчёта

**URL для тестирования:**
- Dev: `https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat-pro.html`
- Legacy: `https://iamaim.ru/wp-content/themes/aim-theme/chat/hermes-chat.html`

**Что нужно протестировать (Task #2):**
1. Открыть hermes-chat-pro.html
2. Отправить URL клиники
3. Проверить Phase Tracker (фазы меняются: pending → working → done)
4. Дождаться Report Preview
5. Тестировать Fallback Form (email submit)

**После успешного теста:**
```bash
ssh aim
cd /var/www/iamaim.ru/wp-content/themes/aim-theme/chat/
mv hermes-chat.html hermes-chat-legacy.html
mv hermes-chat-pro.html hermes-chat.html
```

**Rollback:** См. PHASE09-DEPLOYMENT.md

**HeadroomGuard:** Активен параллельно, не затронут Phase 09 изменениями.

---

## Предыдущая работа (2026-06-27)

### WordPress Golden Master бэкап

**Создан эталонный бэкап WordPress темы:**
- `AIM/wp-golden-master.tar.gz` (8.5 MB)
- `AIM/WP-GOLDEN-MASTER-README.md` — документация
- Содержит reference дизайн: `design-showcase-dual-theme.html` (102 KB)
- Все чат компоненты, assets, theme.css

### Auto-commit система

**Добавлена защита от потери незакоммиченных изменений:**
- `scripts/auto-commit-deploy.sh` — автокоммит перед деплоем
- `.git/hooks/pre-push` — автокоммит перед push
- CLAUDE.md обновлён с правилом Auto-Commit Before Deploy

### Phase 09 откат

**Откат сервера на 2 дня назад:**
- Причина: потеря HeadroomGuard обёртки (не закоммичена, не забэкаплена)
- Phase 09 полностью сохранена: `~/Desktop/phase09-COMPLETE-20260628-022838.tar.gz` (446 KB)
- SOUL.md восстановлен: 104 KB, 1410 строк, 25 июня 22:21
- Hermes app/ файлы: версия от 25 июня (до Phase 09)

---

## План интеграции HeadroomGuard (выполнен)

### Phase 1: Docker Sidecar (✅ DONE)

- [x] Docker-compose конфигурация создана
- [x] Образ скачан: `ghcr.io/chopratejas/headroom:latest`
- [x] Контейнер запущен на порту 8787
- [x] Hermes переключён на прокси
- [x] Healthcheck работает

### Phase 2: Testing (⏳ IN PROGRESS)

- [ ] Тест через iamaim.ru чат
- [ ] Проверка метрик компрессии
- [ ] Валидация качества отчётов
- [ ] Измерение латенси
- [ ] Мониторинг 24 часа

### Phase 3: DeepSeek Fallback (BACKLOG)

HeadroomGuard не умеет fallback между провайдерами. Опции:
1. LiteLLM Router в agent_wrapper.py
2. Portkey как отдельный sidecar
3. Самописный if/else с try/except

---

## Текущая конфигурация production

```yaml
HeadroomGuard:
  container: aim-headroom-proxy
  port: 8787
  upstream: https://api.z.ai/api/coding/paas/v4
  mode: optimize
  compress_tools: false
  keep_turns: 2

Hermes:
  container: aim-hermes
  OMNIROUTE_URL: http://headroom-proxy:8787/v1
  LLM_MODEL: glm-5
  OMNIROUTE_AUTH: 6fd916373bd7462499481201277a7ad0.aCqG4YQTsePka6tI

SOUL.md: 104KB (1410 строк)
AIM tools: 33 зарегистрировано
```

## Файлы интеграции

- `AIM/docker-compose.headroom.yml` — sidecar конфигурация
- `AIM/hermes/HEADROOM-INTEGRATION-PLAN.md` — архитектура и фазы
- `AIM/hermes/HEADROOM-DEPLOY.md` — пошаговый деплой
- `/opt/aim/AIM/.env.headroom` — переменные окружения на сервере

## Commits

- `1af0506` — HeadroomGuard integration prep (28 июня 03:11)

## Что НЕ делать

- ❌ Менять `HEADROOM_COMPRESS_TOOLS` на true (сломает tool calling)
- ❌ Удалять HeadroomGuard без тестирования rollback плана
- ❌ Деплоить без backup текущей конфигурации
