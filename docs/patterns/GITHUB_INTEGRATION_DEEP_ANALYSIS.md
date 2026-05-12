# GitHub Integration: Deep Analysis Pattern

**Дата создания:** 2026-05-13  
**Статус:** КРИТИЧЕСКИ ВАЖНО для Teacher Agent  
**Цель:** Научить систему разбирать найденное до молекул, а не просто документировать

---

## Проблема: Поверхностная интеграция

### Что произошло (2026-05-12)

**Deep Research нашёл 4 репозитория:**
1. python-seo-analyzer (300+ stars)
2. python-for-seo (250+ stars)
3. seo-analyzer (150+ stars)
4. ai-content-detector (180+ stars)

**Что сделали НЕПРАВИЛЬНО:**
- ❌ Нашли репозитории в GitHub Search
- ❌ Прочитали README.md
- ❌ Записали в research report: "Нашли крутой репо с circuit breaker"
- ❌ Написали в спецификацию: "Использовать паттерны из репо X"
- ❌ Считали работу выполненной
- ❌ **НО НЕ КЛОНИРОВАЛИ, НЕ ИЗУЧИЛИ КОД, НЕ ВНЕДРИЛИ**

**Результат:** Работа ради работы, не реальное улучшение системы.

---

## Анализ ошибок: Что пошло не так

### Ошибка 1: Остановились на README

**Что сделали:**
```
1. GitHub Search → нашли репо
2. Открыли README.md
3. Прочитали: "This repo uses circuit breaker pattern"
4. Записали в отчёт: "Found circuit breaker implementation"
5. Закончили работу
```

**Что ДОЛЖНЫ были сделать:**
```
1. GitHub Search → нашли репо
2. git clone <url> ~/temp/research-repos/<name>
3. ls -la → изучили структуру
4. Читали КОД (не README!):
   - src/core/circuit_breaker.py
   - src/utils/retry.py
   - tests/test_circuit_breaker.py
5. Поняли КАК работает (не просто "что есть")
6. Адаптировали в наш код
7. Протестировали
8. Закоммитили
```

**Почему это критично:**
- README говорит "что есть" (маркетинг)
- КОД показывает "как работает" (реальность)
- README: "We use circuit breaker" (бесполезно)
- КОД: `fail_max=5, reset_timeout=60s, exponential_backoff` (полезно!)

### Ошибка 2: Взяли только "лёгкое"

**Что сделали:**
```
Репо 1: python-seo-analyzer
- ✅ Взяли trafilatura (библиотека, легко установить)
- ❌ НЕ взяли circuit breaker (сложно, надо разбираться)
- ❌ НЕ взяли retry logic (сложно)
- ❌ НЕ взяли rate limiting (сложно)

Итог: 1 из 4 репо, только простое
```

**Что ДОЛЖНЫ были сделать:**
```
Репо 1: python-seo-analyzer
- ✅ trafilatura (библиотека)
- ✅ circuit breaker (изучить, адаптировать)
- ✅ retry logic (изучить, адаптировать)
- ✅ rate limiting (изучить, адаптировать)

Репо 2: ai-content-detector
- ✅ DistilBERT (изучить, адаптировать)
- ✅ Perplexity calculation (изучить, адаптировать)
- ✅ Burstiness analysis (изучить, адаптировать)

Репо 3: python-for-seo
- ✅ API integration patterns (изучить, адаптировать)
- ✅ Configuration management (изучить, адаптировать)

Репо 4: seo-analyzer
- ✅ Caching patterns (изучить, адаптировать)
- ✅ Error handling (изучить, адаптировать)

Итог: 4 из 4 репо, ВСЁ ценное
```

**Почему это критично:**
- Мы строим ЛУЧШИЙ сервис, не самый дешёвый
- "Лёгкое" = то, что все делают (нет преимущества)
- "Сложное" = то, что мало кто делает правильно (конкурентное преимущество)
- Trafilatura есть у всех → не даёт преимущества
- Circuit breaker + AI detection + retry logic → даёт преимущество

### Ошибка 3: Остановились на 1 из 4 репо

**Что сделали:**
```
Репо 1: python-seo-analyzer ✅ (изучили)
Репо 2: python-for-seo ❌ (не изучили)
Репо 3: seo-analyzer ❌ (не изучили)
Репо 4: ai-content-detector ❌ (не изучили)

Сказали: "Готово!"
```

**Что ДОЛЖНЫ были сделать:**
```
Репо 1: python-seo-analyzer ✅
Репо 2: python-for-seo ✅
Репо 3: seo-analyzer ✅
Репо 4: ai-content-detector ✅

Только после изучения ВСЕХ → "Готово!"
```

**Почему это критично:**
- Research нашёл 4 репо не просто так
- Каждый репо решает свою часть проблемы
- Пропустить 3 из 4 = потерять 75% ценности
- Это как купить машину без колёс, двигателя и руля

### Ошибка 4: Не разобрали до молекул

**Что сделали:**
```
Нашли: "This repo uses circuit breaker"
Записали: "Use circuit breaker pattern"
Закончили
```

**Что ДОЛЖНЫ были сделать:**
```
Нашли: "This repo uses circuit breaker"

Разобрали до молекул:
1. Какая библиотека? pybreaker
2. Какие параметры? fail_max=5, reset_timeout=60s
3. Как интегрируется? Decorator @circuit_breaker
4. Какие edge cases? Half-open state, manual reset
5. Как тестируется? Mock failures, check state transitions
6. Какие метрики? Prometheus counters for failures/successes
7. Как логируется? structlog with context

Внедрили:
- Установили pybreaker
- Создали wrapper с нашими параметрами
- Добавили в base client
- Написали тесты
- Добавили метрики
- Протестировали

Закончили
```

**Почему это критично:**
- "Use circuit breaker" = бесполезная информация
- Параметры, edge cases, тесты = полезная информация
- Без деталей невозможно внедрить правильно
- Детали = разница между "работает" и "работает в production"

---

## Правильный процесс: Разбор до молекул

### Шаг 1: Клонирование

```bash
cd ~/temp/research-repos
git clone <url> <name>
cd <name>
```

**Цель:** Получить доступ к коду, не только к README.

### Шаг 2: Изучение структуры

```bash
ls -la
find . -name "*.py" | head -20
cat requirements.txt
```

**Цель:** Понять архитектуру проекта.

### Шаг 3: Чтение ключевых файлов

**НЕ читать:**
- README.md (маркетинг)
- CONTRIBUTING.md (для контрибьюторов)
- LICENSE (юридическое)

**ЧИТАТЬ:**
- `src/core/*.py` (основная логика)
- `src/utils/*.py` (утилиты)
- `tests/*.py` (как используется)
- `requirements.txt` (зависимости)
- `config/*.yaml` (конфигурация)

**Цель:** Понять КАК работает, не просто "что есть".

### Шаг 4: Разбор до молекул

**Для каждого паттерна/инструмента:**

1. **Что это?**
   - Название библиотеки/паттерна
   - Назначение

2. **Как работает?**
   - Алгоритм
   - Параметры
   - Edge cases

3. **Как интегрируется?**
   - Где в коде используется
   - Как подключается
   - Зависимости

4. **Как тестируется?**
   - Unit tests
   - Integration tests
   - Edge cases

5. **Какие метрики?**
   - Что измеряется
   - Как логируется
   - Как мониторится

6. **Какие проблемы решает?**
   - Зачем нужно
   - Какие баги предотвращает
   - Какие edge cases покрывает

**Пример: Circuit Breaker**

```python
# 1. Что это?
from pybreaker import CircuitBreaker

# 2. Как работает?
breaker = CircuitBreaker(
    fail_max=5,              # Открыть после 5 ошибок
    reset_timeout=60,        # Попытка закрыть через 60s
    exclude=[ValueError],    # Не считать ValueError за ошибку
)

# 3. Как интегрируется?
@breaker
def api_call():
    response = requests.get(url)
    return response.json()

# 4. Как тестируется?
def test_circuit_breaker_opens():
    for _ in range(5):
        with pytest.raises(Exception):
            api_call()  # 5 ошибок
    
    assert breaker.current_state == "open"

# 5. Какие метрики?
prometheus_client.Counter('circuit_breaker_failures')
prometheus_client.Gauge('circuit_breaker_state')

# 6. Какие проблемы решает?
# - Предотвращает каскадные сбои
# - Даёт время на восстановление
# - Защищает от thundering herd
```

### Шаг 5: Адаптация в наш код

**НЕ копировать слепо:**
```python
# ❌ НЕПРАВИЛЬНО
# Скопировал весь файл из репо
from their_repo import CircuitBreaker
```

**Адаптировать под наши нужды:**
```python
# ✅ ПРАВИЛЬНО
# Понял как работает, адаптировал под нашу архитектуру
from pybreaker import CircuitBreaker
from our_metrics import prometheus_registry
from our_logging import logger

class OurCircuitBreaker:
    """
    Circuit breaker adapted from python-seo-analyzer.
    
    Source: https://github.com/sethblack/python-seo-analyzer
    Changes:
    - Added Prometheus metrics
    - Added structured logging
    - Integrated with our error handling
    """
    
    def __init__(self, name: str, fail_max: int = 5):
        self.breaker = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=60,
            listeners=[self._on_state_change],
        )
        self.name = name
        self._setup_metrics()
    
    def _setup_metrics(self):
        self.failures = prometheus_registry.counter(
            f'circuit_breaker_{self.name}_failures'
        )
        self.state = prometheus_registry.gauge(
            f'circuit_breaker_{self.name}_state'
        )
    
    def _on_state_change(self, breaker, old_state, new_state):
        logger.info(
            "circuit_breaker_state_change",
            name=self.name,
            old_state=old_state,
            new_state=new_state,
        )
        self.state.set(1 if new_state == "open" else 0)
```

### Шаг 6: Тестирование

```python
def test_our_circuit_breaker():
    breaker = OurCircuitBreaker("test_api")
    
    # Тест 1: Открывается после 5 ошибок
    for _ in range(5):
        with pytest.raises(Exception):
            breaker.call(failing_function)
    
    assert breaker.breaker.current_state == "open"
    
    # Тест 2: Метрики обновляются
    assert breaker.failures.get() == 5
    assert breaker.state.get() == 1
    
    # Тест 3: Логи записываются
    assert "circuit_breaker_state_change" in caplog.text
```

### Шаг 7: Документирование

```python
"""
Circuit Breaker Implementation

Source: python-seo-analyzer (https://github.com/sethblack/python-seo-analyzer)
Adapted: 2026-05-13

What we took:
- pybreaker library (fail_max=5, reset_timeout=60s)
- State transition logic (closed → open → half-open)
- Listener pattern for state changes

What we added:
- Prometheus metrics integration
- Structured logging with context
- Integration with our error handling

Usage:
    breaker = OurCircuitBreaker("api_name")
    result = breaker.call(api_function, *args, **kwargs)

Testing:
    See tests/test_circuit_breaker.py
"""
```

---

## Правила для Teacher Agent

### Правило 1: Всегда клонировать

**ЗАПРЕЩЕНО:**
- Читать только README
- Полагаться на описание в research report
- Считать работу выполненной без клонирования

**ОБЯЗАТЕЛЬНО:**
- `git clone <url> ~/temp/research-repos/<name>`
- Изучить структуру: `ls -la`, `find . -name "*.py"`
- Читать КОД, не документацию

### Правило 2: Разбирать до молекул

**ЗАПРЕЩЕНО:**
- "Нашли circuit breaker" (поверхностно)
- "Используют trafilatura" (бесполезно)
- "Есть retry logic" (не конкретно)

**ОБЯЗАТЕЛЬНО:**
- Какая библиотека? pybreaker
- Какие параметры? fail_max=5, reset_timeout=60s
- Как интегрируется? Decorator @circuit_breaker
- Как тестируется? Mock failures, check state
- Какие edge cases? Half-open state, manual reset
- Какие метрики? Prometheus counters

### Правило 3: Брать ВСЁ ценное, не только лёгкое

**ЗАПРЕЩЕНО:**
- Взять только библиотеку (trafilatura)
- Пропустить сложное (circuit breaker, AI detection)
- Остановиться на первом найденном

**ОБЯЗАТЕЛЬНО:**
- Изучить ВСЕ паттерны в репо
- Взять и лёгкое (библиотеки), и сложное (архитектура)
- Приоритет: сложное > лёгкое (больше преимущества)

### Правило 4: Изучить ВСЕ репо из research

**ЗАПРЕЩЕНО:**
- Изучить 1 из 4 репо
- Сказать "готово" после первого репо
- Пропустить репо, если URL не работает

**ОБЯЗАТЕЛЬНО:**
- Изучить ВСЕ репо из research report
- Если URL не работает → WebSearch/Brave для поиска
- Если застрял → спросить пользователя (Мишу)
- Только после изучения ВСЕХ → "готово"

### Правило 5: Внедрить, не просто документировать

**ЗАПРЕЩЕНО:**
- Записать в спецификацию: "Use circuit breaker"
- Добавить в TODO: "Implement retry logic"
- Оставить на потом

**ОБЯЗАТЕЛЬНО:**
- Создать файл с кодом
- Адаптировать под нашу архитектуру
- Написать тесты
- Протестировать
- Закоммитить
- Только после внедрения → "готово"

---

## Чеклист для Teacher Agent

Перед тем как сказать "готово", проверь:

### ✅ Клонирование
- [ ] Все репо из research клонированы в `~/temp/research-repos/`
- [ ] Структура каждого репо изучена (`ls -la`, `find`)
- [ ] requirements.txt каждого репо прочитан

### ✅ Изучение кода
- [ ] Прочитаны ключевые файлы (src/core/, src/utils/)
- [ ] Прочитаны тесты (tests/)
- [ ] Понятна архитектура каждого репо

### ✅ Разбор до молекул
- [ ] Для каждого паттерна/инструмента:
  - [ ] Название библиотеки/паттерна
  - [ ] Параметры и конфигурация
  - [ ] Алгоритм работы
  - [ ] Edge cases
  - [ ] Интеграция в код
  - [ ] Тестирование
  - [ ] Метрики и логирование

### ✅ Взято ВСЁ ценное
- [ ] Не только "лёгкое" (библиотеки)
- [ ] Но и "сложное" (архитектурные паттерны)
- [ ] Приоритет отдан сложному (больше преимущества)

### ✅ Все репо изучены
- [ ] Репо 1: изучено и внедрено
- [ ] Репо 2: изучено и внедрено
- [ ] Репо 3: изучено и внедрено
- [ ] Репо 4: изучено и внедрено
- [ ] Если URL не работал → нашли альтернативу

### ✅ Внедрение
- [ ] Код адаптирован в наш проект
- [ ] Файлы созданы (не TODO)
- [ ] Тесты написаны
- [ ] Тесты проходят
- [ ] Зависимости добавлены в requirements.txt
- [ ] Код закоммичен

### ✅ Документирование
- [ ] Источник указан (URL репо)
- [ ] Что взяли (конкретно)
- [ ] Что изменили (адаптация)
- [ ] Как использовать (примеры)

---

## Примеры: Правильно vs Неправильно

### Пример 1: Circuit Breaker

**❌ НЕПРАВИЛЬНО:**
```
Research report: "Found circuit breaker in python-seo-analyzer"
Specification: "Use circuit breaker pattern"
Implementation: TODO
```

**✅ ПРАВИЛЬНО:**
```
1. Клонировали: git clone https://github.com/sethblack/python-seo-analyzer
2. Изучили: src/http.py, line 45-67
3. Разобрали:
   - Библиотека: pybreaker
   - Параметры: fail_max=5, reset_timeout=60s
   - Интеграция: Decorator @circuit_breaker
   - Edge cases: Half-open state, manual reset
4. Адаптировали: AIM/src/aim/subagents/api_clients/circuit_breaker.py
5. Протестировали: tests/test_circuit_breaker.py (9 tests passing)
6. Закоммитили: feat: add circuit breaker from python-seo-analyzer
```

### Пример 2: AI Content Detection

**❌ НЕПРАВИЛЬНО:**
```
Research report: "Found AI detector with 94% accuracy"
Specification: "Use DistilBERT for AI detection"
Implementation: TODO
```

**✅ ПРАВИЛЬНО:**
```
1. Клонировали: git clone https://github.com/Fahad-Ali-Khan-ca/NLP-Final-Project
2. Изучили: src/features.py, src/ensemble.py
3. Разобрали:
   - Linguistic features: TTR, hapax ratio, readability
   - Perplexity: 2^entropy
   - Burstiness: Gini coefficient of word frequencies
   - Ensemble: 0.3 baseline + 0.7 transformer
4. Адаптировали: AIM/src/aim/subagents/utils/ai_content_detector.py
5. Упростили: Statistical only (no ML models for speed)
6. Протестировали: Correctly distinguishes human vs AI text
7. Закоммитили: feat: add AI content detector from NLP-Final-Project
```

### Пример 3: API Integration

**❌ НЕПРАВИЛЬНО:**
```
Research report: "Found Ahrefs Python SDK"
Specification: "Use Ahrefs SDK for backlinks"
Implementation: TODO
```

**✅ ПРАВИЛЬНО:**
```
1. Клонировали: git clone https://github.com/ahrefs/ahrefs-python
2. Изучили: README.md (Configuration, Automatic Retries sections)
3. Разобрали:
   - Retry-After header respect
   - Exponential backoff with jitter
   - max_retries=2 default
   - timeout=60s default
   - Typed exceptions: AuthenticationError, RateLimitError
4. Валидировали: Наш base.py уже содержит эти паттерны!
5. Подтвердили: Наша реализация корректна
6. Документировали: Validated by ahrefs-python official SDK
```

---

## Метрики успеха

### Для одного репо:

- ✅ Клонирован
- ✅ Структура изучена
- ✅ Ключевые файлы прочитаны (3-5 файлов минимум)
- ✅ Разобрано до молекул (параметры, edge cases, тесты)
- ✅ Взято ВСЁ ценное (не только лёгкое)
- ✅ Адаптировано в наш код
- ✅ Протестировано
- ✅ Закоммичено

### Для всего research:

- ✅ ВСЕ репо из research изучены (не 1 из 4, а 4 из 4)
- ✅ Из каждого репо взято ВСЁ ценное
- ✅ Можно показать: "Вот что мы взяли из КАЖДОГО репо"
- ✅ Нет TODO (всё внедрено)
- ✅ Тесты проходят
- ✅ Код в production

---

## Заключение

**Главный принцип:** Разбирать до молекул, не останавливаться на поверхности.

**Для Teacher Agent:**
- Если нашёл новое → клонировать
- Если клонировал → изучить КОД (не README)
- Если изучил → разобрать до молекул (параметры, edge cases, тесты)
- Если разобрал → взять ВСЁ ценное (не только лёгкое)
- Если взял → внедрить (не TODO)
- Если внедрил → протестировать
- Если протестировал → закоммитить
- Только после ВСЕХ шагов → "готово"

**Мы строим ЛУЧШИЙ сервис!** Берём лучшее от лучших, разбираем до молекул, внедряем правильно.

---

**Версия:** 1.0.0  
**Дата:** 2026-05-13  
**Автор:** meAI Architect  
**Статус:** ✅ КРИТИЧЕСКИ ВАЖНО для Teacher Agent
