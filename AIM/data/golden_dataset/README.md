# Golden Dataset

Эталонный датасет для валидации качества CI Deep Analyzer.

## Описание

Golden Dataset содержит 15 реальных медицинских сайтов (10 стоматологий + 5 косметологий) с ожидаемыми метриками качества.

Используется для:
- **Регрессионного тестирования** - проверка, что изменения не ухудшили качество
- **Benchmark** - сравнение с конкурентами (Ahrefs, SEMrush)
- **Валидация** - проверка корректности анализа

## Структура

```
golden_dataset/
├── config.py           # Конфигурация датасета (15 сайтов)
├── results/            # Результаты анализа
│   ├── dental_001.json
│   ├── dental_002.json
│   └── ...
│   └── summary.json    # Сводка по всем сайтам
└── README.md          # Эта документация
```

## Сайты в датасете

### Стоматология (10 сайтов)
1. Tori Clinic - https://toriclinic.ru/
2. Professional Clinic - https://profclinic.ru/
3. CIDK - https://cidk.ru/
4. Frau Clinic - https://frauklinik.ru/
5. Клиника Юлии Щербатовой - https://juliasherbatova.ru/
6. Smile-at-Once - https://smile-at-once.ru/
7. Дентал Гуру - https://dentalguru.ru/
8. Немецкий Имплантологический Центр - https://www.german-implant-center.ru/
9. Зууб - https://zuub.ru/
10. Дентал Фэнтези - https://dentalfantasy.ru/

### Косметология (5 сайтов)
1. Клиника Пирогова - https://pirogov-clinic.ru/
2. Клиника Семейная - https://semeynaya.ru/
3. Клиника Медси - https://medsi.ru/
4. Клиника Чайка - https://chaikamed.ru/
5. Клиника Реновацио - https://renovacio.ru/

## Запуск анализа

```bash
cd /Users/mikhaileliseev/Desktop/Dev/!meAI
python3 AIM/scripts/run_golden_dataset.py
```

**Время выполнения:** ~2-3 часа (15 сайтов × 8-12 минут на сайт)

**Что происходит:**
1. Для каждого сайта запускается CI Deep Analyzer
2. Анализируется до 50 страниц (для скорости)
3. Собираются все 19 метрик (SEO, CWV, Mobile, A11y, Security)
4. Запускается QA Validator для проверки качества
5. Результаты сохраняются в `results/`

## Ожидаемые метрики

### Benchmark (средние значения)
- **Pages Analyzed:** 70
- **Quality Score:** 75/100
- **SEO Coverage:** 85%
- **CWV Score:** 70/100
- **Mobile Score:** 80/100
- **Accessibility Score:** 70/100
- **Security Score:** 85/100

### Validation Rules (минимальные значения)
- **Pages Analyzed:** ≥ 10
- **Quality Score:** ≥ 50
- **SEO Coverage:** ≥ 60%
- **CWV Score:** ≥ 40
- **Mobile Score:** ≥ 50
- **Accessibility Score:** ≥ 40
- **Security Score:** ≥ 60

## Формат результатов

Каждый файл `results/{site_id}.json` содержит:

```json
{
  "site": {
    "id": "dental_001",
    "name": "Tori Clinic",
    "url": "https://toriclinic.ru/",
    "category": "dentistry",
    "expected_metrics": {...}
  },
  "analysis": {
    "name": "Tori Clinic",
    "url": "https://toriclinic.ru/",
    "pages_analyzed": 50,
    "deep_analysis": {
      "quality_score": 75.5,
      "seo_coverage": {...},
      "cwv": {...},
      "mobile": {...},
      "accessibility": {...},
      "security": {...}
    },
    "issues": {
      "total_issues": 15,
      "by_severity": {...}
    }
  },
  "qa_validation": {
    "validation_status": "passed",
    "quality_report": {
      "quality_score": 85.0,
      "completeness_score": 90.0,
      "validity_score": 85.0,
      "consistency_score": 80.0
    }
  },
  "analyzed_at": "2026-05-05T16:00:00"
}
```

## Использование результатов

### 1. Регрессионное тестирование

После изменений в CI Deep Analyzer:

```bash
# Запустить анализ заново
python3 AIM/scripts/run_golden_dataset.py

# Сравнить с предыдущими результатами
python3 AIM/scripts/compare_golden_results.py
```

### 2. Benchmark сравнение

Сравнить с конкурентами:
- Ahrefs: Domain Rating, Organic Traffic
- SEMrush: Authority Score, Organic Keywords
- Наш Quality Score: комплексная метрика

### 3. Spot-check валидация

Ручная проверка случайных сайтов:
1. Выбрать 3-5 случайных сайтов
2. Проверить вручную ключевые метрики
3. Сравнить с результатами анализа
4. Зафиксировать расхождения

## Обновление датасета

### Добавление нового сайта

1. Добавить в `config.py`:
```python
{
    "id": "dental_011",
    "name": "Новая Клиника",
    "url": "https://example.com",
    "category": "dentistry",
    "expected_metrics": {...}
}
```

2. Обновить `total_sites` и `categories`

3. Запустить анализ

### Обновление ожидаемых метрик

После нескольких запусков анализа:
1. Посмотреть фактические результаты
2. Обновить `expected_metrics` в `config.py`
3. Обновить `benchmark_metrics`

## Метрики качества датасета

### Coverage (полнота)
- ✅ 15 сайтов (10 стоматология + 5 косметология)
- ✅ Разные размеры (от 20 до 400 страниц)
- ✅ Разное качество (от 60 до 95 баллов)

### Diversity (разнообразие)
- ✅ Крупные сети (Медси, Семейная)
- ✅ Средние клиники (Tori, CIDK)
- ✅ Небольшие клиники (Щербатова)

### Representativeness (репрезентативность)
- ✅ Типичные медицинские сайты
- ✅ Реальные конкуренты в нише
- ✅ Актуальные данные (2026)

## Частота обновления

- **Еженедельно:** Spot-check 3-5 случайных сайтов
- **Ежемесячно:** Полный анализ всех 15 сайтов
- **Ежеквартально:** Обновление ожидаемых метрик

## История изменений

### v1.0.0 (2026-05-05)
- Создан датасет из 15 сайтов
- 10 стоматологий + 5 косметологий
- Определены ожидаемые метрики
- Созданы validation rules

---

**Создано:** 2026-05-05  
**Версия:** 1.0.0  
**Статус:** Active
