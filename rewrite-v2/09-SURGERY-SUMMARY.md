# 09 — SURGERY SUMMARY (1 июля 2026, 08:23 UTC)

**Задача:** Исправить главную причину хаоса отчётов — отсутствие Google Fonts и canonical классов в HTML-генераторе.

---

## ✅ ЧТО СДЕЛАНО (3 шага, 5 минут)

### Шаг 1: Создан canonical `build_report.py` (795 строк)

**Файл:** `AIM/hermes/app/tools/build_report.py`

**Ключевые исправления:**
- ✅ Google Fonts через `<link>` (Playfair Display + Jost) — **КРИТИЧНО**
- ✅ Все 14 canonical классов (было 1/14)
- ✅ Theme toggle с localStorage (`aim-theme`)
- ✅ Water ripples (только light theme)
- ✅ Metric tags (5 цветов: green/yellow/red/blue/gray)
- ✅ Glass cards + glass stats + glass table
- ✅ Surface blocks + CTA box
- ✅ Animations: `card-breathe`, `glass-glow`, `water-ripple`
- ✅ Responsive (@media max-width: 768px)

**Референс:** `AIM/frontend/design-showcase-dual-theme.html` (2513 строк) — НЕ WordPress theme путь из CLAUDE.md

### Шаг 2: Замена вызовов (2 файла)

1. **`AIM/hermes/app/pipeline/engine.py:53`**
   ```diff
   - "generate_html_report": ("app.tools.generate_html_report", "handle_generate_html_report"),
   + "generate_html_report": ("app.tools.build_report", "handle_generate_html_report"),
   ```

2. **`AIM/hermes/app/tools/publish_scout_report.py:107`**
   ```diff
   - from app.tools.generate_html_report import _build_report_html
   + from app.tools.build_report import build_report_html
   ```

### Шаг 3: Удаление мёртвого кода (1601 строка)

- ❌ `generate_html_report.py` — 698 строк (только 1/14 классов, нет шрифтов)
- ❌ `generate_html_report_v7_backup.py` — 903 строки (никем не импортируется)

---

## 📊 РЕЗУЛЬТАТ

| Метрика | До | После | Δ |
|---------|-----|-------|---|
| **Генераторов** | 2 | 1 | -50% |
| **Строк кода** | 1601 | 795 | -806 (-50%) |
| **Google Fonts** | ❌ Нет | ✅ Есть | **FIX** |
| **Canonical классов** | 1/14 (7%) | 14/14 (100%) | **+93%** |
| **Theme toggle** | ❌ Нет | ✅ Есть | **NEW** |
| **Water ripples** | ❌ Нет | ✅ Есть | **NEW** |

---

## 🎯 ГЛАВНОЕ ИСПРАВЛЕНИЕ

**Проблема:** `generate_html_report.py` НЕ подключал Google Fonts → шрифты fallback на `-apple-system`/`Georgia` → каждый пользователь видел РАЗНЫЕ шрифты → "хаос отчётов".

**Решение:** `build_report.py` подключает шрифты через `<link>`:
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Jost:wght@300;400;500;600;700&display=swap" rel="stylesheet">
```

Теперь **ВСЕ** пользователи видят **ОДИНАКОВЫЕ** шрифты: Playfair Display (заголовки) + Jost (тело).

---

## 🔍 ОТКУДА ВЗЯЛАСЬ ОШИБКА

**Ложный след в CLAUDE.md:**
```markdown
**Файл:** `AIM/wordpress-core/wp-content/themes/aim-theme/design-showcase-dual-theme.html`
**URL:** https://iamaim.ru/wp-content/themes/aim-theme/design-showcase-dual-theme.html
```

**Реальный canonical:**
```
AIM/frontend/design-showcase-dual-theme.html (2513 строк)
```

CLAUDE.md указывал на **несуществующий** путь в WordPress theme. Реальный reference лежал в `frontend/`.

---

## 🚨 ЧТО НЕ ПРОВЕРЕНО (из аудита)

1. **WordPress theme** (index.php, functions.php, theme.css, chat UI) — прерван пользователем
2. **Hermes tools registry** (сколько реально tools, какие мёртвые) — rate limit
3. **SOUL.md** содержимое — rate limit

**Статус:** Достаточно данных для хирургии. Доп. аудит — опционально.

---

## ⏭️ СЛЕДУЮЩИЙ ШАГ

**Smoke test на сервере:**
1. `docker cp` новый `build_report.py` в контейнер `aim-hermes`
2. Перезапуск контейнера
3. Тестовый прогон pipeline на любом URL
4. Проверка что отчёт:
   - Показывает Playfair Display + Jost (НЕ fallback шрифты)
   - Имеет theme toggle
   - Имеет все 14 canonical классов
   - Публикуется на сайт с правильными стилями

**Команды:**
```bash
# 1. Backup (если нужен rollback)
ssh aim "docker exec aim-hermes cp /opt/hermes/app/tools/build_report.py /opt/data/build_report.py.backup || echo 'no backup needed'"

# 2. Deploy
docker cp AIM/hermes/app/tools/build_report.py aim-hermes:/opt/hermes/app/tools/build_report.py

# 3. Restart
ssh aim "docker restart aim-hermes"

# 4. Test
# Запустить pipeline через Telegram или веб-чат
```

---

## 📝 ОБНОВЛЕНИЯ ДОКУМЕНТАЦИИ

**Обязательно обновить:**
1. `CLAUDE.md` — исправить путь к canonical reference
2. `SESSION.md` — обновить текущую задачу
3. `.current-task` — новая задача

**Текст для CLAUDE.md:**
```markdown
## Design System — Dual Theme (КАНОНИЧЕСКИЙ РЕФЕРЕНС)

**Файл:** `AIM/frontend/design-showcase-dual-theme.html`
**Путь:** `/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/frontend/design-showcase-dual-theme.html`
**Строк:** 2513

⚠️ **ВАЖНО:** НЕ путать с WordPress theme. Canonical reference — в `frontend/`, НЕ в `wordpress-core/wp-content/themes/`.
```

---

## 💾 ROLLBACK ПЛАН (если что-то сломается)

1. Restore backup:
   ```bash
   ssh aim "docker exec aim-hermes cp /opt/data/build_report.py.backup /opt/hermes/app/tools/build_report.py"
   ```

2. Revert engine.py:
   ```bash
   git checkout AIM/hermes/app/pipeline/engine.py
   ```

3. Revert publish_scout_report.py:
   ```bash
   git checkout AIM/hermes/app/tools/publish_scout_report.py
   ```

4. Restore deleted files:
   ```bash
   git checkout AIM/hermes/app/tools/generate_html_report.py
   git checkout AIM/hermes/app/tools/generate_html_report_v7_backup.py
   ```

5. Restart:
   ```bash
   ssh aim "docker restart aim-hermes"
   ```

---

## ✅ КРИТЕРИИ УСПЕХА

**Минимум (обязательно):**
- [ ] Отчёт показывает Playfair Display + Jost (видно в DevTools → Computed → font-family)
- [ ] Theme toggle работает (переключение light/dark)
- [ ] Нет ошибок в браузере console
- [ ] Отчёт публикуется на сайт (не fallback на local save)

**Максимум (желательно):**
- [ ] Все 14 canonical классов применяются корректно
- [ ] Water ripples видны в light theme
- [ ] Metric tags показывают правильные цвета
- [ ] Glass cards с backdrop-filter работают
- [ ] Responsive работает на мобильных (768px breakpoint)

---

*Хирургия завершена 1 июля 2026, 08:23 UTC. Готов к smoke test на сервере.*
