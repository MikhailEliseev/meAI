# REPORT-FORMAT-CONTRACT — Контракт LLM ↔ Builder

**Создан:** 1 июля 2026
**Цель:** Зафиксировать, как LLM должна форматировать interpretation, чтобы builder превратил её в красивый HTML отчёт с design system AIM.

---

## 🎯 Суть контракта

**LLM пишет markdown + STATS блок + special syntax.** Builder (`build_report.py`) преобразует:

| Markdown от LLM | HTML в отчёте |
|---|---|
| `## Заголовок` | `<h2>Заголовок</h2>` (Playfair Display, accent цвет) |
| `### Подзаголовок` | `<h3>Подзаголовок</h3>` |
| `=== Заголовок ===` | `<h3>Заголовок</h3>` (для PERPLEXITY-style секций) |
| `**bold**` | `<strong>bold</strong>` |
| `*italic*` | `<em>italic</em>` |
| `` `code` `` | `<code>code</code>` (моноширинный) |
| `[text](url)` | `<a href="url" target="_blank">text</a>` |
| `- item` | `<ul><li>item</li></ul>` |
| `1. item` | `<ol><li>item</li></ol>` |
| `> цитата` | `<blockquote class="surface-block">цитата</blockquote>` |
| `---` (один на строке) | `<hr>` (горизонтальная линия) |
| `\| table \|` | `<div class="glass-table-wrap"><table>...</table></div>` |
| `STATS:` блок | `<div class="glass-stats-wrap">` с карточками метрик |
| `!!green:+24%!!` | `<span class="metric-tag metric-tag-green">+24%</span>` |
| `!!red:-15%!!` | `<span class="metric-tag metric-tag-red">-15%</span>` |
| `!!yellow:warning!!` | `<span class="metric-tag metric-tag-yellow">warning</span>` |
| `!!blue:info!!` | `<span class="metric-tag metric-tag-blue">info</span>` |
| `!!gray:neutral!!` | `<span class="metric-tag metric-tag-gray">neutral</span>` |
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

- !!green:+24% год к году!! — стабильный рост
- Конкретный пункт с **bold акцентом**
- Сильная команда

## Что хромает

- !!red:-15% трафика за квартал!! — проблема
- Конкретная проблема

> Главный стратегический инсайт: позиция клиники на рынке.

## Рекомендация

1. Усилить SEO (!!yellow:12 недель!!)
2. Запустить Instagram

Подробнее: [сайт клиники](https://example.com).

PERPLEXITY_USED: YES — использованы данные о рынке и трендах
```

---

## 🎨 Canonical classes доступные в CSS

Builder автоматически генерирует эти классы:

### `.glass-stats-wrap` + `.glass-stat` (через STATS блок)
2-5 ключевых метрик.

### `.glass-table-wrap` (через markdown таблицы)
Сравнения.

### `.surface-block` (через `> цитата`)
Цитаты, акцентные блоки.

### `.metric-tag-{color}` (через `!!color:text!!`)
5 цветов: green/yellow/red/blue/gray.

### `.section` + `.sec-tag` + `.interpretation`
Задаёт builder. LLM не пишет эти классы.

---

## ⚙️ Технические детали

### Где это работает?

- **Builder:** `AIM/hermes/app/tools/build_report.py:build_report_html()`
- **Parser:** `_interpretation_to_html(content)` → `_markdown_to_html(content)`
- **STATS extractor:** `_extract_stats_block(text)`
- **Table converter:** `_markdown_table_to_html(table_text)`
- **Inline markdown:** `_inline_markdown(text)` (включая `!!tags!!`)
- **Validation:** `validate_interpretation(content)` → score + warnings

### Что делает builder?

```python
html_content = _interpretation_to_html(interpretation)
# Pipeline:
# 1. STATS: → glass-stats-wrap (extracted first)
# 2. | tables | → glass-table-wrap (extracted second)
# 3. Line-by-line processing:
#    - ## / ### / === === → h2/h3
#    - --- → hr
#    - > → blockquote (multi-line aware)
#    - - / * → ul (state-aware)
#    - 1. → ol (state-aware)
#    - paragraph buffering
# 4. Inline markdown on each piece:
#    - `code` (first, protected)
#    - [text](url) (with nested bold)
#    - **bold**
#    - *italic*
#    - !!color:tag!!
# 5. Existing HTML preserved (>2 tags = HTML mode)
```

### Ограничения

1. **STATS: блок** должен начинаться с `STATS:` на отдельной строке
2. **STATS элементы** — формат:
   ```
   - value: "значение"
     label: "подпись"
   ```
3. **Таблицы** — стандартный markdown pipe-синтаксис
4. **Markdown внутри HTML таблиц** — НЕ парсится (используйте plain text)
5. **Существующий HTML** сохраняется если в тексте > 2 тегов

### Edge cases

- Пустой interpretation → пустая секция (skipped)
- `[Ошибка интерпретации: ...]` → `<p class="text-dim">...</p>` (мягкая ошибка)
- LLM написала HTML напрямую → сохраняется
- Смешанный markdown + HTML → если > 2 HTML тегов, весь текст не парсится
- Многострочный blockquote → автоматически объединяется

---

## 🧪 Тестирование

### Unit тесты

```bash
cd AIM/hermes
python3 tests/test_build_report_parser.py     # базовые 8 тестов
python3 tests/test_real_corpus.py              # реальные IPHC данные
```

Покрывает:
1. `_inline_markdown` — bold/italic/code/links/metric-tags
2. `_extract_stats_block` — STATS парсинг (несколько форматов)
3. `_markdown_table_to_html` — таблицы
4. `_markdown_to_html` — полный pipeline
5. `_interpretation_to_html` — оркестратор
6. `validate_interpretation` — validation + scoring
7. Существующий HTML preserved
8. Error messages
9. Empty input
10. === Header === детект (PERPLEXITY-style)
11. Blockquote (включая multi-line)
12. Horizontal rule

### Test corpus

`tests/fixtures/real_iphc_corpus.json` — 11 секций из реального отчёта IPHC.
Используется для регрессионного тестирования.

---

## 🔄 Жизненный цикл

```
1. LLM получает tool_results (данные фазы)
2. LLM пишет interpretation в формате из этого контракта
3. Pipeline сохраняет {PHASE}_interpretation.json: {"content": "..."}
4. Builder (build_report_html) читает все interpretations
5. Для каждой: _interpretation_to_html(content) → HTML
6. HTML вставляется в <div class="section">
7. QC фаза вызывает validate_interpretation() для score + warnings
8. Финальный HTML публикуется в WordPress
```

---

## 📐 Стандарт структуры отчёта (для каждой фазы)

**Обязательные секции (LLM должна выдать):**

1. **Текущее состояние** — 2-3 предложения + STATS блок (2-5 метрик)
2. **Что хорошо / Сильные стороны** — 3-5 буллетов с цифрами и !!tags!!
3. **Что хромает / Проблемы** — 2-4 буллета
4. **Рекомендация** — 1-2 конкретных действия (нумерованный список)

**Желательно (но не обязательно):**

- `> цитата` с главным инсайтом
- `---` разделитель между логическими блоками
- `[text](url)` ссылки на источники

**Дополнительно для некоторых фаз:**

- COMPETITORS — таблица сравнения (markdown)
- TECH AUDIT — STATS с PageSpeed метриками + !!color:значение!!
- FINANCE — STATS с выручкой/прибылью/ростом
- CONTENT PLAN — нумерованный список приоритетов

---

## 🚫 Что НЕ делать

- ❌ Не писать HTML теги напрямую (builder сделает сам)
- ❌ Не использовать `markdown` заголовки `# h1` (h1 = company name)
- ❌ Не превышать 4000 символов interpretation (будет truncated)
- ❌ Не забывать метку PERPLEXITY_USED в конце (YES/NO/N/A)
- ❌ Не использовать `!!purple:...!!` (только 5 цветов: green/yellow/red/blue/gray)
- ❌ Не писать markdown внутри `| table |` ячеек (используйте plain text)

---

## ✅ Чек-лист проверки

- [ ] Все 4 обязательные секции есть (Состояние/Хорошо/Плохо/Рекомендация)
- [ ] STATS блок содержит 2-5 метрик
- [ ] Списки используют `-` или `1.` (не `•` или `*` для ul)
- [ ] Метрика PERPLEXITY_USED в конце (YES/NO/N/A)
- [ ] Длина < 4000 символов
- [ ] Хотя бы 2-3 `!!color:tag!!` для важных цифр
- [ ] Хотя бы 1 `> цитата` с главным выводом
- [ ] Нет «воды» — только конкретные факты с цифрами

---

## 📊 Validation scoring

`validate_interpretation(content)` возвращает score 0-100:

| Feature | Points |
|---|---|
| Has headers (## или ===) | 25 |
| Has lists (- или 1.) | 20 |
| Has **bold** | 15 |
| Has STATS: block | 20 |
| Has > blockquote | 10 |
| Has !!color:tag!! | 10 |
| **Maximum** | **100** |

Хороший interpretation: score >= 70.
Отличный: score >= 90.

QC phase использует score для автоматической оценки качества отчёта.

---

*Этот контракт — единый язык между LLM и builder. Любые изменения в `_markdown_to_html`, `_inline_markdown` или в `_FORMAT_SUFFIX` должны согласовываться с этим документом.*
