# План: Сырые данные из кода + LLM только выводы

## Принцип
**Таблицы и факты формирует Python-код (из точных данных тулов). LLM получает готовые таблицы и делает только аналитические выводы (2-3 предложения).** LLM не может галлюцинировать в таблице — она из кода.

## Архитектура

```
Тулзы (pipeline, Perplexity)
  ↓ raw JSON results
Formatter (Python) ← НОВЫЙ СЛОЙ
  ↓ готовый Markdown (таблицы, факты)
  ├──→ SSE text-delta (пользователь видит таблицы сразу)
  └──→ LLM context ("данные выше — факты, сделай выводы")
        ↓
      LLM генерирует ТОЛЬКО выводы (2-3 предложения)
        ↓
      SSE text-delta (пользователь видит аналитику)
```

## Реализация

### 1. Новый модуль: `hermes-v2/app/formatters/`
```
formatters/
  __init__.py
  competitors.py    ← Markdown таблица конкурентов из find_competitors JSON
  profile.py        ← Профиль клиники из extract_clinic_profile JSON
  overview.py       ← Очистка quick_overview (только факты, убрать аналитику Perplexity)
```

**competitors.py** — форматирует JSON find_competitors в Markdown:
```python
def format_competitors(result_json: str) -> str:
    """Точная таблица конкурентов из pipeline данных."""
    data = json.loads(result_json)
    comps = data.get("competitors", [])
    lines = ["## 📊 Конкуренты (данные ФНС)\n"]
    lines.append("| Конкурент | Выручка/год | Тренд | Врачей | Instagram |")
    lines.append("|---|---|---|---|---|")
    for c in comps:
        brand = c.get("brand_name") or c.get("legal_name") or "?"
        rev = c.get("revenue_year")
        rev_str = f"{rev/1e6:.0f} млн ₽" if rev else "нет данных"
        trend = {"growing": "📈", "declining": "📉", "stable": "➡️"}.get(c.get("revenue_trend"), "—")
        docs = c.get("surgeons_count") or "—"
        ig = c.get("instagram_followers")
        ig_str = f"{ig//1000}K" if ig else "—"
        lines.append(f"| {brand} | {rev_str} | {trend} | {docs} | {ig_str} |")
    return "\n".join(lines)
```

**profile.py** — профиль из структурированных данных:
```python
def format_profile(profile_json: str) -> str:
    """Профиль клиники — только факты из extract_clinic_profile."""
    # ИНН, юрлицо, город, специализация — из JSON, не из LLM
```

**overview.py** — очистка quick_overview от галлюцинаций Perplexity:
```python
def format_overview(overview_text: str, profile_json: str) -> str:
    """Показывает факты из overview, убирает аналитику/выдумки."""
    # Соцсети, врачи — берём из структурированного profile
    # Убираем "unexpected facts", выдуманный трафик, качественные оценки
    # Оставляем только проверяемые факты: ссылки, имена врачей, платформу
```

### 2. Изменение `llm.py` — форматирование перед LLM
В `chat_with_tools()`, после выполнения тулов (Phase 2 complete), перед финальным LLM ходом:

```python
# После всех tool_results, перед LLM text generation:
formatted_blocks = []
if profile_result:
    formatted_blocks.append(("data_block", format_profile(profile_result)))
if overview_result:
    formatted_blocks.append(("data_block", format_overview(overview_result, profile_result)))
if competitors_result:
    formatted_blocks.append(("data_block", format_competitors(competitors_result)))

# Yield data blocks as text-delta (user sees tables immediately)
for _, block_text in formatted_blocks:
    yield ("text", block_text + "\n\n")

# Prepend formatted blocks to LLM context
data_context = "\n\n".join(b for _, b in formatted_blocks)
messages.append({"role": "system", "content": 
    f"Выше показаны точные данные в виде таблиц. "
    f"Твоя задача — сделать выводы (2-3 предложения). "
    f"НЕ повторяй таблицы. НЕ выдумывай цифры. "
    f"Используй только данные из таблиц выше."
})
```

### 3. Обновление `dialogue.py` — промпт
```python
SYSTEM_PROMPT = """Ты — AI-ассистент AIM.

## Базовый сценарий (URL)
Вызови 3 тула одновременно: extract_clinic_profile, quick_overview, find_competitors.

## Формат ответа
ДАННЫЕ (формируются автоматически из точных источников):
- Таблица конкурентов (ФНС: выручка, ИНН, ОКВЭД, тренд)
- Профиль клиники (ИНН, юрлицо, город)

ТВОЯ ЗАДАЧА — только выводы (3-5 предложений):
1. Позиция клиники относительно конкурентов (по выручке)
2. 1-2 конкретных рекомендации (на основе данных из таблиц)
3. Suggestions кнопки

КРИТИЧНО:
- НЕ повторяй таблицы — они уже показаны
- НЕ выдумывай цифры — используй только из таблиц выше
- НЕ упоминай «отзывы», «рейтинг», «трафик» — этих данных нет
- Если данных нет в таблице — не пиши про них
"""
```

### 4. Что НЕ меняется (golden state)
- ❌ CSS, HTML структура чата
- ❌ Сообщения прогресса (_TOOL_MESSAGES)
- ❌ Welcome text
- ❌ Брендинг
- ❌ Markdown рендеринг (marked.js + DOMPurify) — таблицы рендерятся автоматически

## Порядок реализации
1. `formatters/competitors.py` — таблица конкурентов (главное)
2. `formatters/profile.py` — профиль клиники
3. `llm.py` — инъекция formatted blocks
4. `dialogue.py` — обновить промпт
5. Тест на IPHK в чате
6. (опционально) `formatters/overview.py` — очистка Perplexity

## Ожидаемый результат (IPHK в чате)
```
## 📊 Конкуренты (данные ФНС)

| Конкурент | Выручка/год | Тренд | Врачей | Instagram |
|---|---|---|---|---|
| ИПХиК (Вы) | 4,136 млн ₽ | 📈 | — | — |
| СМ-Клиника | 4,561 млн ₽ | 📈 | 38 | 35K |
| Атлас | 1,700 млн ₽ | 📈 | 30 | — |
...

ИПХиК — безусловный лидер по выручке, ближайший конкурент (СМ-Клиника) 
отстаёт незначительно. Рекомендация: усилить SMM-присутствие — 
Instagram 35K у СМ-Клиники vs нет данных у ИПХиК.

[кнопки suggestions]
```

**Никаких галлюцинаций** — таблица из кода, только точные данные. LLM делает выводы по фактам.
