---
title: "Architect Gatekeeper - Фактчекер входящей информации"
type: improvement
created: 2026-05-02
priority: critical
status: design
tags:
  - architect
  - quality-control
  - fact-checking
  - gatekeeper
---

# Architect Gatekeeper - Фактчекер входящей информации

## Проблема

**Что может пойти не так:**
- Пользователь пьян/устал → вбросит чушь
- Ошибся папкой в Obsidian → не тот контекст
- Материал содержит фигню/мусор
- Источник ненадёжный
- Информация неприменима к нашей системе

**Последствия:**
- Wiki засоряется мусором
- Неправильные решения
- Трата времени на обработку чуши
- Потеря фокуса

---

## Решение: Gatekeeper Agent

**Роль:** Привратник / Фейсконтроль для входящей информации

**Задача:** Проверить качество и применимость ПЕРЕД обработкой

---

## Архитектура Gatekeeper

### Этап 1: Первичная проверка (автоматическая)

```python
class GatekeeperAgent:
    """
    Привратник для проверки качества входящей информации
    """
    
    def check_entry(self, raw_file: Path) -> GatekeeperResult:
        """
        Проверить файл перед обработкой
        
        Returns:
            GatekeeperResult с вердиктом и причинами
        """
        checks = [
            self.check_file_size(raw_file),
            self.check_language(raw_file),
            self.check_structure(raw_file),
            self.check_source_reliability(raw_file),
            self.check_relevance(raw_file),
            self.check_quality(raw_file),
            self.check_duplicates(raw_file),
        ]
        
        return self.aggregate_checks(checks)
```

### Этап 2: Проверки

#### Проверка 1: Размер файла

```python
def check_file_size(self, file_path: Path) -> CheckResult:
    """Проверить размер файла"""
    size = file_path.stat().st_size
    
    # Слишком маленький = мусор
    if size < 100:  # < 100 байт
        return CheckResult(
            passed=False,
            severity="high",
            reason="Файл слишком маленький (< 100 байт)",
            suggestion="Возможно, это случайная заметка или мусор"
        )
    
    # Слишком большой = нужна проверка
    if size > 1_000_000:  # > 1 MB
        return CheckResult(
            passed=False,
            severity="medium",
            reason="Файл очень большой (> 1 MB)",
            suggestion="Возможно, это не текст или нужна предобработка"
        )
    
    return CheckResult(passed=True)
```

#### Проверка 2: Язык

```python
def check_language(self, file_path: Path) -> CheckResult:
    """Проверить язык контента"""
    content = self.read_file(file_path)
    
    # Детект языка
    lang = self.detect_language(content)
    
    if lang not in ['ru', 'en']:
        return CheckResult(
            passed=False,
            severity="high",
            reason=f"Неподдерживаемый язык: {lang}",
            suggestion="Поддерживаются только русский и английский"
        )
    
    return CheckResult(passed=True)
```

#### Проверка 3: Структура

```python
def check_structure(self, file_path: Path) -> CheckResult:
    """Проверить структуру документа"""
    content = self.read_file(file_path)
    
    # Проверяем frontmatter
    if not content.startswith('---'):
        return CheckResult(
            passed=False,
            severity="medium",
            reason="Отсутствует frontmatter",
            suggestion="Добавить метаданные (title, source, created)"
        )
    
    # Проверяем минимальное содержание
    if len(content.strip()) < 200:
        return CheckResult(
            passed=False,
            severity="medium",
            reason="Слишком мало контента (< 200 символов)",
            suggestion="Возможно, это заметка-напоминание, а не материал"
        )
    
    return CheckResult(passed=True)
```

#### Проверка 4: Надёжность источника

```python
def check_source_reliability(self, file_path: Path) -> CheckResult:
    """Проверить надёжность источника"""
    frontmatter = self.parse_frontmatter(file_path)
    source = frontmatter.get('source', '')
    
    # Белый список надёжных источников
    trusted_domains = [
        'youtube.com',
        'github.com',
        'anthropic.com',
        'openai.com',
        'arxiv.org',
        'pubmed.ncbi.nlm.nih.gov',
    ]
    
    # Чёрный список ненадёжных
    untrusted_domains = [
        'clickbait.com',
        'spam.com',
    ]
    
    if any(domain in source for domain in untrusted_domains):
        return CheckResult(
            passed=False,
            severity="high",
            reason="Ненадёжный источник",
            suggestion="Источник в чёрном списке"
        )
    
    if not any(domain in source for domain in trusted_domains):
        return CheckResult(
            passed=True,
            severity="low",
            reason="Неизвестный источник",
            suggestion="Рекомендуется ручная проверка"
        )
    
    return CheckResult(passed=True)
```

#### Проверка 5: Применимость (КЛЮЧЕВАЯ)

```python
def check_relevance(self, file_path: Path) -> CheckResult:
    """
    КЛЮЧЕВАЯ ПРОВЕРКА: Применимо ли к нашей системе?
    """
    content = self.read_file(file_path)
    frontmatter = self.parse_frontmatter(file_path)
    
    # Контекст нашей системы
    our_context = {
        'project': 'meAI + AIM Agency',
        'focus': [
            'AI-агенты',
            'медицинский маркетинг',
            'автоматизация',
            'Claude',
            'Python',
            'FastAPI',
            'Obsidian',
        ],
        'not_relevant': [
            'игры',
            'криптовалюты (если не про AI)',
            'политика',
            'развлечения',
        ]
    }
    
    # Анализ применимости через LLM
    prompt = f"""
Проверь применимость материала к нашей системе.

Наш контекст:
- Проект: {our_context['project']}
- Фокус: {', '.join(our_context['focus'])}
- НЕ релевантно: {', '.join(our_context['not_relevant'])}

Материал:
Title: {frontmatter.get('title', 'N/A')}
Source: {frontmatter.get('source', 'N/A')}
Content preview: {content[:500]}...

Вопросы:
1. Применимо ли это к нашей системе? (да/нет)
2. Почему? (1-2 предложения)
3. Какая польза? (конкретно)
4. Риски использования? (если есть)

Ответ в JSON:
{{
  "relevant": true/false,
  "reason": "...",
  "benefit": "...",
  "risks": "..."
}}
"""
    
    # Вызов LLM для анализа
    result = self.call_llm(prompt)
    
    if not result['relevant']:
        return CheckResult(
            passed=False,
            severity="high",
            reason=f"Неприменимо к нашей системе: {result['reason']}",
            suggestion="Пропустить обработку"
        )
    
    if result['risks']:
        return CheckResult(
            passed=True,
            severity="medium",
            reason=f"Применимо, но есть риски: {result['risks']}",
            suggestion="Обработать с осторожностью"
        )
    
    return CheckResult(
        passed=True,
        metadata={
            'benefit': result['benefit'],
            'reason': result['reason']
        }
    )
```

#### Проверка 6: Качество контента

```python
def check_quality(self, file_path: Path) -> CheckResult:
    """Проверить качество контента"""
    content = self.read_file(file_path)
    
    # Проверка на мусор
    garbage_indicators = [
        'asdfasdf',
        'test test test',
        '111111',
        'фывфывфыв',
    ]
    
    if any(indicator in content.lower() for indicator in garbage_indicators):
        return CheckResult(
            passed=False,
            severity="high",
            reason="Обнаружены признаки мусора",
            suggestion="Возможно, пользователь был пьян/устал"
        )
    
    # Проверка на связность
    sentences = content.split('.')
    if len(sentences) < 5:
        return CheckResult(
            passed=False,
            severity="medium",
            reason="Слишком мало предложений (< 5)",
            suggestion="Возможно, это фрагмент или заметка"
        )
    
    return CheckResult(passed=True)
```

#### Проверка 7: Дубликаты

```python
def check_duplicates(self, file_path: Path) -> CheckResult:
    """Проверить на дубликаты"""
    content = self.read_file(file_path)
    frontmatter = self.parse_frontmatter(file_path)
    
    # Проверяем по source
    source = frontmatter.get('source', '')
    if source:
        existing = self.find_by_source(source)
        if existing:
            return CheckResult(
                passed=False,
                severity="high",
                reason=f"Дубликат: уже обработан как {existing.name}",
                suggestion="Пропустить обработку"
            )
    
    # Проверяем по содержимому (similarity)
    similar = self.find_similar_content(content, threshold=0.9)
    if similar:
        return CheckResult(
            passed=False,
            severity="high",
            reason=f"Похожий контент: {similar.name}",
            suggestion="Возможно, дубликат или очень похожий материал"
        )
    
    return CheckResult(passed=True)
```

---

## Workflow с Gatekeeper

### Старый workflow:

```
raw/ → Монитор → Обработка → wiki/
```

### Новый workflow:

```
raw/ → Gatekeeper → [PASS/FAIL] → Монитор → Обработка → wiki/
         ↓
      [FAIL]
         ↓
    quarantine/ (карантин)
```

---

## Результаты проверки

### Вердикт: PASS (зелёный свет)

```
✅ Файл прошёл все проверки
📊 Оценка качества: 9/10
💡 Применимость: Высокая
🎯 Польза: [конкретная польза]
```

### Вердикт: WARN (жёлтый свет)

```
⚠️  Файл прошёл с предупреждениями
📊 Оценка качества: 6/10
💡 Применимость: Средняя
⚠️  Риски: [конкретные риски]
🤔 Рекомендация: Ручная проверка
```

### Вердикт: FAIL (красный свет)

```
❌ Файл НЕ прошёл проверку
📊 Оценка качества: 3/10
💡 Применимость: Низкая
🚫 Причина: [конкретная причина]
💾 Действие: Перемещён в quarantine/
```

---

## Карантин (quarantine/)

**Структура:**

```
obsidian/architect/quarantine/
├── 2026-05-02-failed-quality.md
├── 2026-05-02-not-relevant.md
├── 2026-05-02-duplicate.md
└── README.md
```

**README.md:**

```markdown
# Карантин

Файлы, не прошедшие проверку Gatekeeper.

## Причины попадания:

- Низкое качество
- Неприменимо к системе
- Дубликат
- Ненадёжный источник
- Мусор

## Что делать:

1. Просмотреть файлы
2. Если ошибка Gatekeeper → переместить в raw/
3. Если действительно мусор → удалить
4. Периодически чистить (раз в неделю)
```

---

## Интеграция с монитором

```python
async def process_file(self, file_path: Path) -> None:
    """Обработать один файл"""
    print(f"\n🔍 Обрабатываю: {file_path.name}")
    
    # ШАГ 1: GATEKEEPER (НОВОЕ)
    gatekeeper = GatekeeperAgent(self.wiki_dir, self.quarantine_dir)
    check_result = gatekeeper.check_entry(file_path)
    
    if not check_result.passed:
        print(f"❌ Файл НЕ прошёл проверку Gatekeeper")
        print(f"   Причина: {check_result.reason}")
        print(f"   Действие: Перемещён в quarantine/")
        
        # Перемещаем в карантин
        self.move_to_quarantine(file_path, check_result)
        return
    
    if check_result.severity == "medium":
        print(f"⚠️  Файл прошёл с предупреждениями")
        print(f"   {check_result.reason}")
        print(f"   Рекомендация: {check_result.suggestion}")
    else:
        print(f"✅ Файл прошёл проверку Gatekeeper")
        if check_result.metadata:
            print(f"   Польза: {check_result.metadata.get('benefit', 'N/A')}")
    
    # ШАГ 2: Проверяем, не обработан ли уже
    if self.is_processed(file_path):
        print(f"✅ Уже обработан: {file_path.name}")
        self.processed_files[file_path.name] = self.get_file_hash(file_path)
        return
    
    # ШАГ 3: Умная проверка: читать raw или wiki?
    source_type, source_path = self.should_read_raw_or_wiki(file_path)
    
    # ... остальная обработка
```

---

## Примеры работы

### Пример 1: Пьяная заметка

**Входной файл:**

```markdown
---
title: "asdfasdf"
created: 2026-05-02
---

test test test 111111
фывфывфыв
```

**Результат:**

```
❌ Файл НЕ прошёл проверку Gatekeeper
   Причина: Обнаружены признаки мусора
   Действие: Перемещён в quarantine/2026-05-02-garbage.md
```

### Пример 2: Не тот контекст

**Входной файл:**

```markdown
---
title: "Как заработать на криптовалютах"
source: "https://crypto-scam.com"
---

Купи биткоин и разбогатей!
```

**Результат:**

```
❌ Файл НЕ прошёл проверку Gatekeeper
   Причина: Неприменимо к нашей системе (криптовалюты не в фокусе)
   Действие: Перемещён в quarantine/2026-05-02-not-relevant.md
```

### Пример 3: Дубликат

**Входной файл:**

```markdown
---
title: "BlackHat SEO методы"
source: "https://www.youtube.com/watch?v=uAI7-Y6h__Q"
---

...
```

**Результат:**

```
❌ Файл НЕ прошёл проверку Gatekeeper
   Причина: Дубликат: уже обработан как blackhat-seo-igaming-analysis.md
   Действие: Перемещён в quarantine/2026-05-02-duplicate.md
```

### Пример 4: Хороший материал

**Входной файл:**

```markdown
---
title: "Claude Design для создания сайтов"
source: "https://www.youtube.com/watch?v=16fyyG-IzzM"
---

Раньше платил 100,000₽ за сайт...
```

**Результат:**

```
✅ Файл прошёл проверку Gatekeeper
   Оценка качества: 9/10
   Применимость: Высокая
   Польза: Экономия 100,000₽ на сайт через Claude Design
   
→ Продолжаю обработку...
```

---

## Настройки Gatekeeper

**Конфиг файл:** `.architect/gatekeeper.yaml`

```yaml
gatekeeper:
  enabled: true
  
  checks:
    file_size:
      enabled: true
      min_size: 100  # байт
      max_size: 1000000  # 1 MB
    
    language:
      enabled: true
      allowed: ['ru', 'en']
    
    structure:
      enabled: true
      require_frontmatter: true
      min_content_length: 200
    
    source_reliability:
      enabled: true
      trusted_domains:
        - youtube.com
        - github.com
        - anthropic.com
      untrusted_domains:
        - clickbait.com
    
    relevance:
      enabled: true
      use_llm: true
      our_focus:
        - AI-агенты
        - медицинский маркетинг
        - автоматизация
      not_relevant:
        - игры
        - криптовалюты
    
    quality:
      enabled: true
      garbage_indicators:
        - asdfasdf
        - test test test
    
    duplicates:
      enabled: true
      similarity_threshold: 0.9
  
  quarantine:
    enabled: true
    path: obsidian/architect/quarantine/
    auto_cleanup_days: 7
```

---

## Метрики Gatekeeper

**Отслеживать:**

- Процент прохождения (PASS rate)
- Причины отказов (топ-5)
- Ложные срабатывания (false positives)
- Пропущенный мусор (false negatives)

**Цели:**

- PASS rate: 70-80% (не слишком строго, не слишком мягко)
- False positives: <5%
- False negatives: <2%

---

## Следующие шаги

### Priority 1: Базовый Gatekeeper (завтра)

```python
# Реализовать GatekeeperAgent
# Добавить базовые проверки (размер, язык, структура)
# Интегрировать с монитором
```

### Priority 2: LLM-проверка применимости (эта неделя)

```python
# Добавить check_relevance() с LLM
# Настроить контекст нашей системы
# Тестировать на реальных данных
```

### Priority 3: Карантин (эта неделя)

```python
# Создать quarantine/
# Добавить move_to_quarantine()
# Автоматическая очистка раз в неделю
```

### Priority 4: Метрики и улучшения (следующая неделя)

```python
# Отслеживать метрики
# Анализировать ошибки
# Улучшать проверки
```

---

## Вывод

**Проблема:** Мусор и нерелевантная информация попадает в систему  
**Решение:** Gatekeeper Agent с 7 проверками  
**Результат:** Только качественная и применимая информация в wiki

**Следующий шаг:** Реализовать базовый Gatekeeper завтра

---

**Architect Decision:** Gatekeeper критически важен для качества системы. Приоритет: CRITICAL.
