# Linear Tasks — Наведение порядка в проекте

**Created:** 2026-05-21
**Status:** Ожидает LINEAR_API_KEY

---

## 🔴 HIGH PRIORITY

### 1. Проиндексировать проект в Obsidian
**Labels:** `documentation`, `obsidian`
**Priority:** High

Все vaults должны содержать актуальную базу знаний:
- [ ] architect/wiki/ — индекс, overview, фазы, агенты, технологии
- [ ] AIM/obsidian/operator/ — операционные метрики
- [ ] AIM/obsidian/seo-magister/ — SEO стратегии, конкуренты
- [ ] AIM/obsidian/content-magister/ — контент-план, качество
- [ ] AIM/obsidian/ads-magister/ — кампании, статистика
- [ ] AIM/obsidian/analytics-magister/ — метрики, атрибуция
- [ ] Для каждого vault: index.md, log.md, заполненные категории wiki/

### 2. Очистить мусор на сервере
**Labels:** `server`, `cleanup`
**Priority:** High

В ~/meAI/ на сервере 80+ файлов в корне:
- [ ] Удалить дубликаты SESSION_*.md (20+ файлов)
- [ ] Удалить старые SUMMARY/SESSION_COMPLETE (15+ файлов)
- [ ] Перенести отчёты в obsidian/architect/raw/
- [ ] Удалить .canvas файлы (не используются)
- [ ] Оставить только: CLAUDE.md, SESSION.md, CHECKPOINTS.md, ROADMAP.md

### 3. Синхронизировать Obsidian vaults local ↔ server
**Labels:** `obsidian`, `infrastructure`
**Priority:** High

Сейчас vaults на сервере и локально рассинхронизированы:
- [ ] Добавить Obsidian vaults в git (сейчас они не трекаются)
- [ ] Или настроить rsync при деплое
- [ ] Проверить что vaults идентичны после синхронизации

---

## 🟡 MEDIUM PRIORITY

### 4. Настроить Teacher Agent
**Labels:** `agents`, `learning`
**Priority:** Medium

Teacher Agent должен запускаться каждые 2-4 недели:
- [ ] Проверить GitHub на новые репо/паттерны
- [ ] Обновить знания субагентов
- [ ] Создать Learning Report в obsidian/teacher/

### 5. Добавить .playwright-mcp в .gitignore
**Labels:** `git`, `cleanup`
**Priority:** Medium

Логи Playwright засоряют git status:
- [ ] Добавить `.playwright-mcp/` в .gitignore
- [ ] Добавить `reports/` в .gitignore
- [ ] Добавить `logs/` в .gitignore

### 6. Установить LINEAR_API_KEY
**Labels:** `infrastructure`, `integrations`
**Priority:** Medium

- [ ] Получить API ключ на linear.app
- [ ] Добавить LINEAR_API_KEY в .env (локально и сервер)
- [ ] Проверить работу LinearClient

---

## 🟢 LOW PRIORITY

### 7. Починить conftest.py (зависимости)
**Labels:** `tests`, `bug`
**Priority:** Low

Тесты не запускаются с conftest из-за отсутствующих зависимостей:
- numpy, jinja2, email-validator уже установлены
- Возможно ещё зависимости — прогнать pip install -r requirements.txt

### 8. Pydantic V2 migration для AdsSettings
**Labels:** `tech-debt`, `pydantic`
**Priority:** Low

AdsSettings использует class-based Config (deprecated):
- ```python
  # Заменить:
  class Config:
      env_file = ".env"
      env_prefix = "ADS_"
  # На:
  model_config = ConfigDict(env_file=".env", env_prefix="ADS_")
  ```
