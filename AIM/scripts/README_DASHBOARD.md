# Operator Dashboard

CLI Dashboard для визуализации и управления результатами CI анализа.

## Возможности

- 📊 **Список всех анализов** - просмотр истории анализов
- 🔍 **Детальный просмотр** - подробная информация по каждому конкуренту
- ⚖️ **Сравнение конкурентов** - side-by-side сравнение метрик
- 📤 **Экспорт отчётов** - Markdown, CSV форматы
- 🎨 **Rich UI** - красивые таблицы, панели, цвета

## Установка

```bash
pip install rich
```

Или:

```bash
pip install -r requirements.txt
```

## Использование

### Интерактивный режим

```bash
python3 AIM/scripts/operator_dashboard.py
```

Меню:
1. 📊 List all analyses - показать все доступные анализы
2. 🔍 View analysis details - детальный просмотр анализа
3. ⚖️ Compare competitors - сравнение конкурентов
4. 📤 Export to Markdown - экспорт в Markdown
5. 📤 Export to CSV - экспорт в CSV
6. 🚪 Exit - выход

## Примеры

### Просмотр списка анализов

```
📊 Available Analyses

                                Analysis History                                
╭──────┬──────────────────────┬──────────────┬─────────────────────────────────╮
│ #    │ Date                 │ Competitors  │ File                            │
├──────┼──────────────────────┼──────────────┼─────────────────────────────────┤
│ 1    │ 2026-05-05 16:19:02  │ 5            │ deep_analysis_20260505_161902.… │
│ 2    │ 2026-05-05 16:06:27  │ 5            │ deep_analysis_20260505_160627.… │
│ 3    │ 2026-05-05 15:51:05  │ 1            │ deep_analysis_20260505_155105.… │
╰──────┴──────────────────────┴──────────────┴─────────────────────────────────╯
```

### Детальный просмотр

```
╭─────────────────────────── Competitor #1 ───────────────────────────────╮
│                                                                          │
│ 🏢 Tori Clinic                                                           │
│ 🔗 https://toriclinic.ru/                                                │
│                                                                          │
│ 📊 Quality Score: 75.5/100                                               │
│ 📄 Pages Analyzed: 50                                                    │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯

                        Metrics Breakdown                        
┌────────────────────┬────────────┬─────────────────────────────┐
│ Category           │ Score      │ Details                     │
├────────────────────┼────────────┼─────────────────────────────┤
│ SEO                │ ✓          │ Title: 50/50, Desc: 45/50   │
│ Core Web Vitals    │ 65/100     │ LCP: 2.8s, CLS: 0.15        │
│ Mobile             │ 80/100     │ Viewport: 100%, Resp: 90%   │
│ Accessibility      │ 70/100     │ Contrast: 80%, ARIA: 85%    │
│ Security           │ 85/100     │ HTTPS: 100%, HSTS: 80%      │
└────────────────────┴────────────┴─────────────────────────────┘
```

### Сравнение конкурентов

```
📊 COMPETITOR COMPARISON

                    Quality Metrics Comparison                    
╭────────────────────┬──────────┬────────┬────────┬────────┬──────┬──────────╮
│ Competitor         │ Quality  │ Pages  │ CWV    │ Mobile │ A11y │ Security │
├────────────────────┼──────────┼────────┼────────┼────────┼──────┼──────────┤
│ Tori Clinic        │ 75.5     │ 50     │ 65     │ 80     │ 70   │ 85       │
│ Professional Clinic│ 72.3     │ 45     │ 60     │ 75     │ 65   │ 80       │
│ CIDK               │ 78.1     │ 55     │ 70     │ 85     │ 75   │ 90       │
╰────────────────────┴──────────┴────────┴────────┴────────┴──────┴──────────╯

🏆 Analysis Summary

✨ Best Quality Score: CIDK (78.1/100)
📄 Most Pages Analyzed: CIDK (55 pages)
⚡ Best Core Web Vitals: CIDK (70/100)
```

## Экспорт

### Markdown

Экспортирует полный отчёт в Markdown формат:

```markdown
# CI Analysis Report

**Date:** 2026-05-05T16:19:02
**Competitors Analyzed:** 5
**Quality:** deep

---

## Competitors

### 1. Tori Clinic

**URL:** https://toriclinic.ru/
**Quality Score:** 75.5/100
**Pages Analyzed:** 50

#### Metrics

| Category | Score | Details |
|----------|-------|---------|
| SEO | ✓ | Title: 50/50, Desc: 45/50 |
| Core Web Vitals | 65/100 | LCP: 2.8s, CLS: 0.15 |
...
```

Файл сохраняется в: `AIM/data/exports/analysis_YYYYMMDD_HHMMSS.md`

### CSV

Экспортирует данные в CSV формат для анализа в Excel/Google Sheets:

```csv
Name,URL,Quality Score,Pages Analyzed,CWV Score,Mobile Score,Accessibility Score,Security Score
Tori Clinic,https://toriclinic.ru/,75.5,50,65,80,70,85
Professional Clinic,https://profclinic.ru/,72.3,45,60,75,65,80
...
```

Файл сохраняется в: `AIM/data/exports/analysis_YYYYMMDD_HHMMSS.csv`

## Структура данных

Dashboard читает данные из:
- `AIM/data/ci-deep/` - результаты CI Deep Analyzer
- `AIM/data/golden_dataset/results/` - результаты Golden Dataset (будущее)

Формат файлов: `deep_analysis_YYYYMMDD_HHMMSS.json`

## Технологии

- **Rich** - красивый CLI UI (таблицы, панели, цвета)
- **Python 3.11+** - async/await, type hints
- **JSON** - формат хранения данных

## Roadmap

- [ ] Web UI версия (FastAPI + React)
- [ ] Графики и charts (plotly)
- [ ] Benchmark сравнение с Golden Dataset
- [ ] Экспорт в HTML с интерактивными графиками
- [ ] Фильтрация и поиск по анализам
- [ ] Тренды и история изменений
- [ ] Alerts и уведомления

---

**Создано:** 2026-05-05  
**Версия:** 1.0.0  
**Статус:** Production Ready
