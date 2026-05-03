---
title: "Monitor + Gatekeeper Integration - Analysis & Next Steps"
type: workflow
created: 2026-05-03T08:32
priority: critical
status: active
tags:
  - monitor
  - gatekeeper
  - workflow
  - improvement
---

# Monitor + Gatekeeper Integration - Анализ и улучшения

## Проблема, которую обнаружили

**Ошибка в workflow:** Monitor обрабатывает raw-файлы, но **не создаёт wiki-документы**.

### Текущий flow (НЕПРАВИЛЬНЫЙ):

```
raw/file.md
    ↓
Monitor обнаруживает
    ↓
Gatekeeper проверяет (7 checks)
    ↓
PASS → файл остаётся в raw/ со статусом "processed"
    ↓
❌ ПРОБЛЕМА: wiki-документ НЕ создаётся
    ↓
❌ ПРОБЛЕМА: я читаю raw-транскрипт вместо wiki
```

### Правильный flow (LLM Wiki Pattern):

```
raw/file.md
    ↓
Monitor обнаруживает
    ↓
Gatekeeper проверяет (7 checks)
    ↓
PASS → Monitor создаёт wiki-документ в нужной категории
    ↓
raw/file.md обновляется:
  - status: processed
  - output: [[wiki-file-name]]
    ↓
✅ Читаем wiki-документ, НЕ raw
```

## Что нарушается

### 1. LLM Wiki Pattern (Karpathy)

**Правило:** Raw = immutable sources, Wiki = compiled knowledge

**Нарушение:**
- Raw-файлы остаются необработанными
- Wiki-слой не создаётся
- Нет compiled knowledge, только raw sources

### 2. Frontmatter Contract

**Правило:** `status: processed` + `output: [[wiki-file]]`

**Нарушение:**
- Файл помечается как processed
- Но output не указывается
- Невозможно найти wiki-документ

### 3. Read Strategy

**Правило:** Проверить frontmatter → читать wiki, если processed

**Нарушение:**
- Monitor имеет метод `should_read_raw_or_wiki()`
- Но wiki-файл не существует
- Fallback на raw-чтение

## Почему это критично

### 1. Перегрузка контекста

**Проблема:**
- Raw-транскрипты = 200-300 строк
- Wiki-документы = 50-100 строк (сжатые инсайты)
- Читая raw → тратим 3x больше токенов

**Пример:**
- `raw/20260502-2320-blackhat-seo.md` — исходный транскрипт (не читали)
- `wiki/sources/2026-05-02-blackhat-seo.md` — 242 строки compiled knowledge
- Но я читал wiki, потому что он УЖЕ существовал (создан вручную)

### 2. Потеря структуры

**Проблема:**
- Raw = неструктурированный поток мыслей
- Wiki = категоризированные инсайты
- Без wiki → нет структуры знаний

**Пример из wiki/sources/2026-05-02-blackhat-seo.md:**
```markdown
## Ключевые инсайты
### 1. Вирусный трафик
### 2. Китайский метод
### 3. AI-агенты для автоматизации
### 4. Стратегия массового запуска
```

Эта структура **не существует** в raw-файле.

### 3. Невозможность синтеза

**Проблема:**
- Синтез требует чтения wiki из разных категорий
- Если wiki не создаются → синтез невозможен
- Connections/ остаются пустыми

**Пример синтеза (который мы НЕ можем сделать):**
```
wiki/sources/2026-05-02-blackhat-seo.md (AI-агенты)
    +
wiki/agents/medical-content-agent.md (медицинский контент)
    =
connections/ai-content-automation-for-medical.md (синтез)
```

## Решение: 3 уровня автоматизации

### Level 1: Manual Processing (ТЕКУЩИЙ)

**Как работает:**
1. Monitor обнаруживает файл
2. Gatekeeper проверяет качество
3. Monitor генерирует промпт
4. **Человек (я) вручную создаёт wiki-документ**
5. Человек обновляет frontmatter в raw/

**Плюсы:**
- ✅ Полный контроль качества
- ✅ Гибкость в структурировании

**Минусы:**
- ❌ Требует ручной работы
- ❌ Медленно
- ❌ Не масштабируется

### Level 2: Semi-Automatic (СЛЕДУЮЩИЙ ШАГ)

**Как работает:**
1. Monitor обнаруживает файл
2. Gatekeeper проверяет качество
3. Monitor вызывает Claude CLI для создания wiki
4. Claude создаёт wiki-документ автоматически
5. Monitor обновляет frontmatter в raw/
6. **Человек проверяет результат**

**Реализация:**
```python
async def create_wiki_document(self, file_path: Path, file_type: str) -> Path:
    """Создать wiki-документ через Claude CLI"""
    
    # Читаем raw-файл
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Генерируем промпт для Claude
    prompt = f"""
Создай wiki-документ из raw-файла.

Raw-файл: {file_path.name}
Тип: {file_type}

Контент:
{content}

Задача:
1. Извлеки ключевые инсайты
2. Структурируй по категориям
3. Создай frontmatter с метаданными
4. Определи категорию wiki (concepts/technologies/strategies/agents/workflows/projects/sources/connections)
5. Верни путь к созданному файлу

Формат ответа:
wiki/category/filename.md
"""
    
    # Вызываем Claude CLI
    result = subprocess.run(
        ['claude', '--model', 'claude-sonnet-4-20250514', '-p', prompt],
        capture_output=True,
        text=True,
        timeout=300
    )
    
    # Парсим путь к wiki-файлу
    wiki_path = self.wiki_dir / result.stdout.strip()
    
    return wiki_path
```

**Плюсы:**
- ✅ Автоматизация рутины
- ✅ Быстрее, чем ручная обработка
- ✅ Человек проверяет качество

**Минусы:**
- ❌ Требует Claude CLI
- ❌ Может создавать некачественные wiki
- ❌ Нужна проверка каждого документа

### Level 3: Fully Automatic (БУДУЩЕЕ)

**Как работает:**
1. Monitor обнаруживает файл
2. Gatekeeper проверяет качество
3. Monitor создаёт wiki автоматически
4. Monitor обновляет frontmatter
5. Monitor обновляет index.md
6. Monitor логирует в log.md
7. **Всё без участия человека**

**Дополнительно:**
- Автоматический синтез (connections/)
- Автоматический lint (проверка здоровья wiki)
- Автоматические алерты при проблемах

**Плюсы:**
- ✅ Полная автоматизация
- ✅ Масштабируется
- ✅ Работает 24/7

**Минусы:**
- ❌ Сложная реализация
- ❌ Риск некачественных wiki
- ❌ Требует мониторинга

## Рекомендация: Level 2 (Semi-Automatic)

**Почему:**
1. **Баланс:** автоматизация + контроль качества
2. **Реализуемо:** можно сделать за 1-2 часа
3. **Безопасно:** человек проверяет результат
4. **Масштабируемо:** обрабатывает 10-20 файлов/день

**Что нужно:**
1. Добавить метод `create_wiki_document()` в Monitor
2. Интегрировать вызов Claude CLI
3. Обновлять frontmatter в raw/ после создания wiki
4. Логировать операции в wiki/log.md

## Next Steps для синтеза инсайтов

После того, как wiki-документы создаются автоматически:

### 1. Synthesis Agent (Priority: HIGH)

**Задача:** Читать wiki из разных категорий и создавать connections/

**Пример:**
```python
# Читаем wiki-документы
seo_insights = read_wiki("sources/2026-05-02-blackhat-seo.md")
medical_agent = read_wiki("agents/medical-content-agent.md")
competitor_agent = read_wiki("agents/competitor-intelligence-agent.md")

# Синтезируем
synthesis = synthesize([seo_insights, medical_agent, competitor_agent])

# Создаём connection
create_connection("ai-medical-marketing-automation.md", synthesis)
```

**Результат:**
- Автоматические синтезы для AIM Agency
- Actionable plans на основе инсайтов
- Connections между разными областями знаний

### 2. Query Agent (Priority: MEDIUM)

**Задача:** Отвечать на вопросы, читая wiki (не raw)

**Пример:**
```python
question = "Как автоматизировать контент-маркетинг для медицинских клиник?"

# Ищем релевантные wiki-документы
relevant_docs = search_wiki(question)

# Читаем и синтезируем ответ
answer = query_wiki(question, relevant_docs)

# Создаём новую wiki-страницу с ответом
create_wiki_page("workflows/medical-content-automation.md", answer)
```

### 3. Lint Agent (Priority: LOW)

**Задача:** Проверять здоровье wiki

**Проверки:**
- Orphan pages (нет ссылок на них)
- Broken links (ссылки на несуществующие страницы)
- Contradictions (противоречия между документами)
- Outdated info (устаревшая информация)
- Missing connections (пропущенные связи)

## Метрики успеха

### До улучшений:
- ❌ Wiki-документы создаются вручную
- ❌ Raw-файлы читаются напрямую
- ❌ Нет автоматического синтеза
- ❌ Connections/ пустые

### После Level 2:
- ✅ Wiki-документы создаются автоматически
- ✅ Raw-файлы обрабатываются в wiki
- ✅ Frontmatter обновляется автоматически
- ✅ Человек проверяет качество

### После Level 3:
- ✅ Полная автоматизация
- ✅ Автоматический синтез
- ✅ Connections/ заполняются
- ✅ Actionable plans для AIM Agency

## Вывод

**Текущая проблема:** Monitor обнаруживает и классифицирует, но не создаёт wiki.

**Решение:** Добавить Level 2 (Semi-Automatic) с вызовом Claude CLI.

**Следующий шаг:** Реализовать `create_wiki_document()` в Monitor.

**Конечная цель:** Автоматический синтез инсайтов в actionable plans для AIM Agency.

---

**Architect Decision:** Реализовать Level 2 (Semi-Automatic) как следующий приоритет.
