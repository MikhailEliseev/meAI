# REPORT-FORMAT-CONTRACT — Контракт LLM ↔ Builder

**Создан:** 1 июля 2026
**Цель:** Зафиксировать, как LLM должна форматировать interpretation, чтобы builder превратил её в красивый HTML отчёт с design system AIM.

---

## 🎯 Суть контракта

**LLM пишет markdown + STATS блок.** Builder (`build_report.py`) преобразует:

| Markdown от LLM | HTML в отчёте |
|---|---|
| `## Заголовок` | `<h2>Заголовок</h2>` (Playfair Display, accent цвет) |
| `### Подзаголовок` | `<h3>Подзаголовок</h3>` |
| `**bold**` | `<strong>bold</strong>` |
| `*italic*` | `<em>italic</em>` |
| `- item` | `<ul><li>item</li></ul>` |
| `1. item` | `<ol><li>item</li></ol>` |
| `\| table \|` | `<div class="glass-table-wrap"><table>...</table></div>` |
| `STATS:` блок | `<div class="glass-stats-wrap">` с карточками метрик |
| Существующий HTML | Сохраняется как есть |

---

## 📋 Шаблон interpretation для КАЖДОЙ фазы

```markdown
## Текущее состояние

Краткое описание в 2-3 предложениях с ключевыми фактами.

STATS:
- value: "4,1 млрд ₽"
  label: "Выручка 2024"
- value: "+24%"
  label: "Рост за год"
- value: "1200"
  label: "Сотрудников"

## Что хорошо

- Конкретный пункт 1 (с цифрой)
- Конкретный пункт 2 (с фактом)
- Конкретный пункт 3

## Что хромает

- Конкретная проблема 1
- Конкретная проблема 2

## Рекомендация

1. Конкретное действие
2. Конкретное действие

PERPLEXITY_USED: YES — использованы данные о рынке и трендах
```

---

## 🎨 Canonical classes доступные в CSS

Builder автоматически генерирует эти классы из markdown:

### `.glass-stats-wrap` + `.glass-stat`
Через STATS блок. Использовать для 2-5 ключевых метрик.

### `.glass-table-wrap`
Через markdown таблицы. Использовать для сравнений.

### `.section` + `.sec-tag` + `.interpretation`
Задаёт builder. LLM не пишет эти классы.

### Остальные классы (LLM пишет сама если нужно)

| Класс | Когда использовать |
|---|---|
| `.metric-tag-green` | Положительная метрика |
| `.metric-tag-yellow` | Предупреждение |
| `.metric-tag-red` | Проблема |
| `.metric-tag-blue` | Информация |
| `.metric-tag-gray` | Нейтральное |
| `.surface-block` | Цитата/accent |
| `.card-glass` | Glass card |
| `.text-dim` | Бледный текст |
| `.text-meta` | Метаданные |
| `.text-accent-link` | Акцентная ссылка |

---

## ⚙️ Технические детали

### Где это работает?

- **Builder:** `AIM/hermes/app/tools/build_report.py:build_report_html()`
- **Parser:** `_interpretation_to_html(content)` → `_markdown_to_html(content)`
- **STATS extractor:** `_extract_stats_block(text)`
- **Table converter:** `_markdown_table_to_html(table_text)`

### Что делает builder?

```python
html_content = _interpretation_to_html(interpretation)
# → STATS: → glass-stats-wrap
# → tables → glass-table-wrap
# → markdown → headers, lists, paragraphs, bold, italic
# → existing HTML preserved
```

### Ограничения

1. **STATS: блок** должен начинаться с `STATS:` на отдельной строке
2. **STATS элементы** — формат:
   ```
   - value: "значение"
     label: "подпись"
   ```
3. **Таблицы** — стандартный markdown pipe-синтаксис
4. **Существующий HTML** сохраняется если в тексте > 2 тегов

### Edge cases

- Пустой interpretation → пустая секция (skipped)
- `[Ошибка интерпретации: ...]` → `<p class="text-dim">...</p>` (мягкая ошибка)
- LLM написала HTML напрямую (например, glass-stats-wrap) → сохраняется
- Смешанный markdown + HTML → если > 2 HTML тегов, весь текст не парсится

---

## 🧪 Тестирование

Тестовый скрипт: `tests/test_build_report_parser.py`

```bash
cd AIM/hermes
python3 tests/test_build_report_parser.py
```

Покрывает:
1. `_inline_markdown` — bold/italic
2. `_extract_stats_block` — STATS парсинг
3. `_markdown_table_to_html` — таблицы
4. `_markdown_to_html` — полный pipeline
5. `_interpretation_to_html` — оркестратор
6. Существующий HTML preserved
7. Error messages
8. Empty input

---

## 🔄 Жизненный цикл

```
1. LLM получает tool_results (данные фазы)
2. LLM пишет interpretation в формате из этого контракта
3. Pipeline сохраняет {PHASE}_interpretation.json: {"content": "..."}
4. Builder (build_report_html) читает все interpretations
5. Для каждой: _interpretation_to_html(content) → HTML
6. HTML вставляется в <div class="section">
7. Финальный HTML публикуется в WordPress
```

---

## 📐 Стандарт структуры отчёта (для каждой фазы)

**Обязательные секции (LLM должна выдать):**

1. **Текущее состояние** — 2-3 предложения + STATS блок (2-5 метрик)
2. **Что хорошо / Сильные стороны** — 3-5 буллетов с цифрами
3. **Что хромает / Проблемы** — 2-4 буллета
4. **Рекомендация** — 1-2 конкретных действия (нумерованный список)

**Дополнительно для некоторых фаз:**

- COMPETITORS — таблица сравнения
- TECH AUDIT — STATS с PageSpeed метриками
- FINANCE — STATS с выручкой/прибылью/ростом
- CONTENT PLAN — нумерованный список приоритетов

---

## 🚫 Что НЕ делать

- ❌ Не писать HTML теги напрямую (кроме как в STATS блоке)
- ❌ Не использовать `markdown` заголовки `# h1` (h1 = company name)
- ❌ Не превышать 4000 символов interpretation
- ❌ Не забывать метку PERPLEXITY_USED в конце

---

## ✅ Чек-лист проверки

- [ ] Все 4 обязательные секции есть (Состояние/Хорошо/Плохо/Рекомендация)
- [ ] STATS блок содержит 2-5 метрик
- [ ] Списки используют `-` или `1.` (не `•` или `*` для ul)
- [ ] Метрика PERPLEXITY_USED в конце (YES/NO/N/A)
- [ ] Длина < 4000 символов
- [ ] Нет «воды» — только конкретные факты с цифрами

---

*Этот контракт — единый язык между LLM и builder. Любые изменения в `_markdown_to_html` или в prompts должны согласовываться с этим документом.*
