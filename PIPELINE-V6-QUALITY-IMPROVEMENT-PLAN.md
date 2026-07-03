# Pipeline v6 — Quality Improvement Plan

**Дата:** 3 июля 2026  
**Статус:** После успешного запуска Pipeline v5 E2E (3 клиента прошли полностью)  
**Git tag:** `pipeline-v5-working-e2e` (commit `7a16dfa`)  
**Backup:** `/opt/hermes-backups/pipeline-v5-working-20260703-124722/`

---

## 🎯 Контекст и мотивация

После успешного запуска Pipeline v5 (3 июля 2026, 3 клиента прошли E2E) был проведён детальный анализ качества данных в финальных отчётах. Сравнение **эталонного отчёта** (ИПХиК, старая версия) с **новым отчётом** (Pipeline v5, session 71b5e599-5fd) выявило критические проблемы с качеством данных.

### Проблемы пользователя:
1. **Неверные или недостоверные данные** в отчётах
2. **Мало конкурентов или их данных**
3. **Скучная подача, нет WOW-эффекта**

---

## 📊 Root Cause Analysis: что пошло не так

### Сравнительная таблица качества

| Параметр | Эталонный отчёт (старая версия) | Pipeline v5 (session 71b5e599-5fd) | Δ |
|----------|--------------------------------|-------------------------------------|---|
| **Конкуренты** | 8 конкурентов с финансами | **0 конкурентов** ❌ | -100% |
| **Финансы конкурентов** | Seline 2.3 млрд, Олимп 1.9 млрд, GMTClinic 742 млн... | **НЕТ ДАННЫХ** | -100% |
| **Врачи с Instagram** | 15 врачей с handles | **5 врачей БЕЗ handles** | -67% |
| **Instagram метрики** | Мельников 318K, avg лайки, просмотры | **НЕТ МЕТРИК** | -100% |
| **Контент-анализ врачей** | Deep audit 20 Reels × 4 врача | **НЕТ АНАЛИЗА** | -100% |
| **Топ-5 страхов пациентов** | 5 конкретных страхов с форумов | **НЕТ ДАННЫХ** | -100% |
| **Заголовок отчёта** | "ИПХиК vs 8 конкурентов" | **"Iphk vs 0 конкурентов"** 😱 | Катастрофа |

---

## 🔍 Детальные находки из сырых данных

### ПРОБЛЕМА #1: Конкуренты — катастрофический провал данных

**Файл:** `/opt/hermes-data/sessions-archive/71b5e599-5fd/data/COMPETITORS_find_competitors.json`

**Что вернул `find_competitors`:**
```json
{
  "competitors": [
    {
      "brand_name": "ЛАНЦЕТЪ",
      "revenue_year": null,
      "website": "https://lancette.iphk.ru/",
      "data_source": "dadata",
      "match_reason": "масштаб отличается, услуги отличаются, оценочные данные"
    }
  ],
  "is_megalopolis": true
}
```

**Диагноз:**
- `find_competitors` вернул **только 1 конкурента** — и это **ЛАНЦЕТЪ** (подразделение самого ИПХиК, не конкурент!)
- Fallback на Perplexity **НЕ СРАБОТАЛ**, хотя код есть (`find_competitors.py:311-327`)
- Причина: код проверяет `if not competitors:`, но **1 конкурент ≠ пустой список**
- Система посчитала, что данные есть, и не запустила Perplexity fallback

**Что должно было быть:**
- Минимум 5-8 конкурентов с финансами из ФНС
- Perplexity fallback при низком качестве (не только при пустоте)

---

### ПРОБЛЕМА #2: Врачи — отсутствие ключевого инструмента

**Файл:** `/opt/hermes-data/sessions-archive/71b5e599-5fd/data/KEY PERSONS_run_doctor_dossiers.json`

**Что произошло:**
- `find_doctor_handles` **вообще не вызывался** (файл отсутствует в `data/`)
- Вместо него вызван `run_doctor_dossiers` с параметром `doctor_name: "Iphk"` (название клиники, а не врач!)
- `run_instagram_content` не мог сработать без handles

**Что вернул `run_doctor_dossiers`:**
```json
{
  "doctor_name": "Iphk",
  "total_profiles_found": 3,
  "visibility": "низкая — врач почти невидим онлайн",
  "platforms": [...]
}
```

**Диагноз:**
- Инструмент искал профили "врача" с именем "Iphk" 🤦
- `find_doctor_handles` не в списке **обязательных** инструментов в SOUL.md
- Без handles невозможен deep Instagram audit

**Что должно было быть:**
- `find_doctor_handles(url="https://iphk.ru")` → 15 врачей с Instagram handles
- `run_instagram_content(doctors=[top 5 handles])` → метрики аудитории, контент-анализ

---

### ПРОБЛЕМА #3: Interpretation "спас ситуацию", но неправильно

**Файл:** `COMPETITORS_interpretation.json`

LLM при интерпретации **попытался объяснить провал данных как feature**:

> "Это не сбой системы, а снимок реальности: ведущие игроки эстетической медицины в Москве почти не присутствуют в цифровом пространстве."

**Диагноз:**
- Это **ложь** — эталонный отчёт показывает 8 конкурентов с финансами и Instagram
- LLM "оправдывает" плохие данные вместо того, чтобы сообщить о проблеме
- Нет validation перед публикацией отчёта

---

## 🔧 План исправлений (Pipeline v6)

### Приоритет P0: Критические фиксы (блокируют качество)

#### **FIX #1: Улучшить fallback логику в find_competitors**

**Файл:** `AIM/hermes/app/tools/find_competitors.py`

**Проблема:**  
Fallback срабатывает только при `len(competitors) == 0`, но не при низком качестве (1 конкурент без данных).

**Решение:**

1. Добавить helper для оценки качества:

```python
def _competitors_quality_score(competitors: list) -> float:
    """Оценка качества списка конкурентов (0-1).
    
    Критерии:
    - Есть выручка: +0.4
    - Есть website: +0.2
    - Не affiliated с клиентом: +0.2
    - rating/reviews: +0.2
    """
    if not competitors:
        return 0.0
    
    scores = []
    for c in competitors:
        score = 0.0
        if c.get("revenue_year"):
            score += 0.4
        if c.get("website") and not c.get("website", "").startswith(("http://lancette", "https://lancette")):
            score += 0.2
        if c.get("rating") and c.get("reviews_count", 0) > 10:
            score += 0.2
        if c.get("brand_name") and c.get("brand_name") != "ЛАНЦЕТЪ":
            score += 0.2
        scores.append(score)
    
    return sum(scores) / len(scores)
```

2. Изменить условие fallback (строка 311):

```python
# БЫЛО:
if not competitors:
    push_tool_progress("competitors", "🔄 Google Maps пустой — спрашиваю Perplexity...")
    
# СТАЛО:
if not competitors or len(competitors) < 3 or _competitors_quality_score(competitors) < 0.3:
    push_tool_progress(
        "competitors", 
        f"🔄 Найдено {len(competitors)} конкурентов (мало или низкое качество) — "
        f"спрашиваю Perplexity о топ-конкурентах (3-pass)..."
    )
```

**Impact:** Fallback будет срабатывать при низком качестве данных, не только при пустоте.

**Тестирование:**
```bash
# Проверить, что fallback срабатывает при quality_score < 0.3
# Проверить, что fallback срабатывает при len < 3
```

---

#### **FIX #2: Добавить ОБЯЗАТЕЛЬНЫЙ вызов find_doctor_handles в SOUL.md**

**Файл:** `AIM/hermes/skills/aim/SOUL.md`

**Проблема:**  
`find_doctor_handles` не в списке обязательных инструментов (строки 29-60).

**Решение:**

1. Добавить в список обязательных (строка 39):

```markdown
9. `find_doctor_handles` — врачи с сайта + Instagram handles — **ВЫЗЫВАЙ ПЕРВЫМ в секции врачей**
10. `run_instagram_content` — deep audit Reels (ТОЛЬКО если find_doctor_handles вернул handles)
```

2. Добавить правило после строки 54:

```markdown
**⚠️ ПРАВИЛО РАБОТЫ С ВРАЧАМИ:**

1. **ВСЕГДА** вызывай `find_doctor_handles(url=...)` ПЕРВЫМ для секции врачей
2. Если find_doctor_handles вернул handles (len > 0) → вызывай `run_instagram_content(doctors=handles[:5])`
3. Если find_doctor_handles вернул пустоту → вызывай `perplexity_search("врачи [название клиники] Instagram ФИО")` → ручной поиск
4. `run_doctor_dossiers` вызывай ТОЛЬКО с конкретными ФИО врачей, НЕ с названием клиники

**АНТИ-ПАТТЕРН:** ❌ `run_doctor_dossiers(doctor_name="Iphk")`  
**ПРАВИЛЬНО:** ✅ `find_doctor_handles(url="https://iphk.ru")` → получаем список врачей → `run_doctor_dossiers(doctor_name="Захаров Антон Игоревич")`
```

**Impact:** Гарантирует вызов find_doctor_handles в каждой сессии.

---

#### **FIX #3: Добавить validation в generate_html_report**

**Файл:** `AIM/hermes/app/tools/generate_html_report.py` или где обрабатывается narrative_md

**Проблема:**  
Нет проверки минимального качества данных перед генерацией отчёта.

**Решение:**

Добавить pre-check перед генерацией:

```python
def _validate_report_quality(narrative_md: str, session_data: dict) -> tuple[bool, list[str]]:
    """Валидация минимального качества отчёта.
    
    Returns:
        (is_valid, list_of_warnings)
    """
    warnings = []
    
    # 1. Проверка длины
    if len(narrative_md) < 15000:
        warnings.append(f"⚠️ Отчёт слишком короткий: {len(narrative_md)} символов (минимум 15000)")
    
    # 2. Проверка конкурентов
    competitors = session_data.get("COMPETITORS", {})
    comp_list = competitors.get("competitors", [])
    if len(comp_list) < 3:
        warnings.append(f"⚠️ Найдено только {len(comp_list)} конкурентов (минимум 3)")
    
    # 3. Проверка врачей
    key_persons = session_data.get("KEY PERSONS", {})
    doctors_with_handles = [d for d in key_persons.get("doctors", []) if d.get("instagram")]
    if len(doctors_with_handles) < 3:
        warnings.append(f"⚠️ Найдено только {len(doctors_with_handles)} врачей с Instagram (минимум 3)")
    
    # 4. Проверка метрик
    if "4.8" not in narrative_md and "5.0" not in narrative_md:
        warnings.append("⚠️ Нет конкретных рейтингов клиники в отчёте")
    
    is_valid = len(warnings) < 2  # Не больше 1 критичного предупреждения
    
    return is_valid, warnings


# В handler generate_html_report:
is_valid, warnings = _validate_report_quality(narrative_md, session_data)

if not is_valid:
    logger.error(f"Report quality validation failed: {warnings}")
    push_wow_comment(
        f"⚠️ Качество отчёта ниже минимума:\n" + "\n".join(warnings), 
        "error"
    )
    return json.dumps({
        "error": "Report quality below minimum threshold",
        "warnings": warnings,
        "suggestion": "Retry pipeline with named_competitors or manual doctor list"
    })
```

**Impact:** Блокирует публикацию низкокачественных отчётов.

---

### Приоритет P1: Важные улучшения (повышают качество)

#### **FIX #4: Улучшить interpretation prompt для конкурентов**

**Файл:** Где генерируется interpretation_prompt для COMPETITORS (найти в engine.py или phases.py)

**Проблема:**  
LLM "объясняет" провал данных вместо того, чтобы запросить больше.

**Решение:**

Добавить в промпт:

```markdown
**ПРАВИЛО МИНИМАЛЬНОГО КАЧЕСТВА:**

Если в competitors < 3 конкурентов ИЛИ у большинства нет revenue_year:
1. НЕ пиши "это нормально" или "снимок реальности"
2. СООБЩИ: "⚠️ Данные неполные. Рекомендую вызвать find_competitors с параметром named_competitors=[список вручную]"
3. Предложи 5-7 известных конкурентов для ручного поиска

**Примеры конкурентов для пластической хирургии Москвы:**
Seline, GMTClinic, Фрау Клиник, Олимп Клиник, ОН КЛИНИК, Клазко, Доктор Пластик

**АНТИ-ПАТТЕРН:**
❌ "Это не сбой системы, а снимок реальности: ведущие игроки почти не присутствуют в цифровом пространстве."

**ПРАВИЛЬНО:**
✅ "⚠️ Автоматический поиск нашёл только 1 конкурента без финансов. Это может быть ошибка парсинга. Рекомендую повторный запуск с named_competitors: ['Seline', 'GMTClinic', 'Фрау Клиник']."
```

**Impact:** LLM перестанет "оправдывать" плохие данные.

---

#### **FIX #5: Добавить автоматический re-run при низком качестве**

**Файл:** `AIM/hermes/app/pipeline/engine.py`

**Идея:**  
После фазы COMPETITORS проверять качество и автоматически перезапускать с named_competitors.

**Псевдокод:**

```python
# После выполнения фазы COMPETITORS
competitors_data = state.get("COMPETITORS", {})
comp_list = competitors_data.get("competitors", [])

if len(comp_list) < 3 or _competitors_quality_score(comp_list) < 0.4:
    logger.warning("⚠️ Low quality competitors data, retrying with Perplexity...")
    
    # Автоматически вызываем Perplexity для поиска названий
    perplexity_competitors = await _get_top_competitors_from_perplexity(state["url"])
    
    # Перезапускаем find_competitors с named_competitors
    retry_result = await tool_handlers["find_competitors"](
        url=state["url"],
        named_competitors=perplexity_competitors
    )
    
    # Обновляем state
    state["COMPETITORS"] = json.loads(retry_result)
    logger.info("✅ Retry successful, found %d competitors", len(state["COMPETITORS"]["competitors"]))
```

**Impact:** Автоматическое исправление без участия пользователя.

---

### Приоритет P2: Опциональные улучшения (полировка)

#### **FIX #6: Добавить логирование и мониторинг качества**

**Файлы:** Все tool handlers

**Решение:**

```python
# В конце каждого handler
from app.main import push_wow_comment

if len(result["competitors"]) < 3:
    push_wow_comment(
        f"⚠️ find_competitors вернул только {len(result['competitors'])} конкурентов",
        "warning"
    )
```

**Impact:** Visibility для отладки.

---

#### **FIX #7: Создать эталонный тест**

**Новый файл:** `AIM/hermes/tests/test_iphk_quality.py`

```python
def test_iphk_quality_standard():
    """Тест на соответствие эталону iphk.ru.
    
    Минимальные требования:
    - >= 5 конкурентов
    - >= 8 врачей с Instagram handles
    - >= 2 врача с метриками (followers, avg_likes)
    - Длина отчёта >= 20000 символов
    """
    session_data = load_session("71b5e599-5fd")
    
    assert len(session_data["COMPETITORS"]["competitors"]) >= 5
    assert len([d for d in session_data["KEY PERSONS"]["doctors"] if d.get("instagram")]) >= 8
    assert len(session_data["narrative_md"]) >= 20000
```

**Impact:** Предотвращает регрессию качества.

---

## 🗂️ Архитектурное улучшение: доступ к сырым данным

### Проблема до миграции

Сырые данные сессий сохранялись **внутри Docker volume** `hermes_data:/opt/data`, который:
- ❌ НЕ доступен напрямую на хосте
- ❌ НЕ удобен для анализа (требуется docker exec)
- ❌ НЕ может быть использован базой знаний

### Решение: миграция на bind mount

**Дата:** 3 июля 2026, 13:21 UTC  
**Выполнено:**

1. Создана директория на хосте: `/opt/hermes-data/`
2. Скопировано 68 сессий из Docker volume на хост
3. Изменён `docker-compose.yml`:
   ```yaml
   # БЫЛО:
   volumes:
     - hermes_data:/opt/data
   
   # СТАЛО:
   volumes:
     - /opt/hermes-data:/opt/data
   ```
4. Контейнер перезапущен успешно

**Новая структура доступа:**

```
На хосте (прямой доступ):
/opt/hermes-data/sessions-archive/{session_id}/
├── metadata.json              # Метаданные сессии
├── data/                      # Все файлы с сырыми данными
│   ├── COMPETITORS_find_competitors.json
│   ├── COMPETITORS_interpretation.json
│   ├── KEY PERSONS_run_doctor_dossiers.json
│   ├── PERPLEXITY_perplexity_search.json
│   └── ... (все 13 фаз + интерпретации)
└── report.html               # Финальный HTML отчёт

Внутри контейнера (без изменений):
/opt/data/sessions-archive/{session_id}/
```

**Преимущества:**
- ✅ Прямой доступ к сырым данным с хоста без docker exec
- ✅ Простой backup: `tar -czf backup.tar.gz /opt/hermes-data/`
- ✅ База знаний может читать напрямую
- ✅ Re-interpretation возможна: берём сырые данные, запускаем новый промпт
- ✅ Легкий анализ и отладка

---

## 📅 План внедрения

### Неделя 1 (критично):
1. ✅ **FIX #1:** Улучшить fallback логику find_competitors
2. ✅ **FIX #2:** Добавить find_doctor_handles в SOUL.md обязательно
3. ✅ **FIX #3:** Добавить validation в generate_html_report

### Неделя 2 (важно):
4. ✅ **FIX #4:** Улучшить interpretation prompt для конкурентов
5. ✅ **FIX #5:** Автоматический re-run при низком качестве

### Неделя 3 (полировка):
6. ✅ **FIX #6:** Логирование и мониторинг качества
7. ✅ **FIX #7:** Эталонный тест на регрессию

---

## 🎯 Ожидаемый результат Pipeline v6

После внедрения всех фиксов Pipeline v6 будет генерировать отчёты с качеством эталона:

✅ **5-8 конкурентов** с финансами из ФНС  
✅ **10-15 врачей** с Instagram handles  
✅ **Детальные метрики** аудитории (followers, avg likes, просмотры)  
✅ **Контент-анализ** топ-4 врачей (20 Reels × врач)  
✅ **5 топ-страхов пациентов** с форумов  
✅ **20,000+ символов** с инсайтами  
✅ **Автоматический fallback** при провале данных  
✅ **Validation** перед публикацией

---

## 📂 Референсы и файлы

### Эталонная сессия (для сравнения):
- **Файл:** `/Users/mikhaileliseev/Downloads/ИПХиК (2).html`
- **Качество:** 8 конкурентов, 15 врачей, детальные метрики

### Проблемная сессия (для анализа):
- **Session ID:** `71b5e599-5fd`
- **Путь на сервере:** `/opt/hermes-data/sessions-archive/71b5e599-5fd/`
- **Путь локально:** `/Users/mikhaileliseev/Desktop/Dev/meAI_1/analysis/71b5e599-5fd/`
- **URL отчёта:** https://iamaim.ru/59ddggd3
- **Дата:** 3 июля 2026, 12:27 UTC

### Бэкап Pipeline v5:
- **Путь:** `/opt/hermes-backups/pipeline-v5-working-20260703-124722/`
- **Содержит:** 52 сессии, код Hermes
- **Git tag:** `pipeline-v5-working-e2e`

### Код:
- **find_competitors.py:** `AIM/hermes/app/tools/find_competitors.py`
- **find_doctor_handles.py:** `AIM/hermes/app/tools/find_doctor_handles.py`
- **SOUL.md:** `AIM/hermes/skills/aim/SOUL.md`
- **session_archive.py:** `AIM/hermes/app/tools/session_archive.py`
- **docker-compose.yml:** `/opt/aim/AIM/docker-compose.yml`

---

## 🔄 Workflow для следующих улучшений

1. **Взять копию кода:**
   ```bash
   cd /Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM
   git checkout -b pipeline-v6-quality-improvements
   ```

2. **Внедрить FIX #1-#3** (критичные)

3. **Тестировать на проблемной сессии:**
   ```bash
   # Повторить запуск с iphk.ru
   # Проверить, что:
   # - >= 5 конкурентов с финансами
   # - >= 8 врачей с Instagram handles
   # - Validation срабатывает при низком качестве
   ```

4. **Коммит и tag:**
   ```bash
   git add -A
   git commit -m "feat: Pipeline v6 quality improvements (FIX #1-#3)"
   git tag pipeline-v6-quality-fixes
   git push origin pipeline-v6-quality-improvements
   git push --tags
   ```

5. **Deploy на production:**
   ```bash
   ssh aim "cd /opt/aim/AIM && git pull && docker compose build hermes && docker compose up -d hermes"
   ```

6. **E2E тест:**
   - Повторить 3 клиента: arclinic.ru, mira-med.ru, iphk.ru
   - Сравнить качество отчётов с эталоном
   - Зафиксировать результат в `SESSION.md`

---

## ✅ Checklist перед внедрением

- [ ] Backup текущей версии создан
- [ ] FIX #1 реализован и протестирован
- [ ] FIX #2 добавлен в SOUL.md
- [ ] FIX #3 добавлен в generate_html_report
- [ ] Unit-тесты написаны
- [ ] E2E тест на iphk.ru пройден
- [ ] Документация обновлена
- [ ] Git tag создан
- [ ] Deploy на production выполнен

---

## 📝 Заметки

- **Проблема Perplexity или интерпретации?** Ответ: **НЕ Perplexity**. Проблема в tool orchestration и fallback логике. Perplexity работает корректно, но не вызывается при низком качестве данных от Google Maps.

- **Почему старый отчёт был лучше?** Потому что старая версия имела более агрессивную логику fallback и вызывала find_doctor_handles обязательно. Pipeline v5 оптимизировал количество вызовов, но потерял качество.

- **Re-interpretation старых сессий:** После внедрения v6 можно взять сырые данные из `/opt/hermes-data/sessions-archive/` и переинтерпретировать с новыми промптами.

---

**Автор анализа:** Claude Sonnet 4.5  
**Дата создания:** 3 июля 2026, 13:53 UTC  
**Версия документа:** 1.0
