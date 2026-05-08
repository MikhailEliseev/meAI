# SEO Агент - Структура

## Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                      SEO Agent                          │
│                   (Execution Layer)                     │
└─────────────────────────────────────────────────────────┘
                           │
                           │ наследуется от
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     Base Agent                          │
│  • execute_task()                                       │
│  • get_capabilities()                                   │
│  • receive_task()                                       │
│  • report_result()                                      │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐    ┌──────────┐
    │Event Bus│      │Obsidian │    │ Database │
    │         │      │  Vault  │    │          │
    └─────────┘      └─────────┘    └──────────┘
```

## Основные функции

```
SEOAgent
├── analyze_competitors()
│   ├── Сбор данных о конкурентах
│   ├── Анализ ключевых слов
│   └── Сохранение в vault
│
├── research_keywords()
│   ├── Генерация семантического ядра
│   ├── Анализ частотности
│   └── Кластеризация
│
├── optimize_content()
│   ├── Анализ контента
│   ├── Рекомендации по улучшению
│   └── SEO-аудит
│
└── monitor_positions()
    ├── Отслеживание позиций
    ├── Уведомления об изменениях
    └── Отчеты
```

## Поток данных

```
YOU/Architect
      │
      │ стратегическая задача
      ▼
   Operator
      │
      │ тактическая задача
      ▼
  Event Bus ──────► SEO Agent
      │                 │
      │                 │ выполнение
      │                 ▼
      │            ┌─────────┐
      │            │ Анализ  │
      │            │ Подбор  │
      │            │Оптимиз. │
      │            │Монитор. │
      │            └─────────┘
      │                 │
      │                 │ результат
      ▼                 ▼
  Event Bus ◄────── SEO Agent
      │
      │ агрегированный отчет
      ▼
   Operator
      │
      ▼
     YOU
```

## Obsidian Vault Structure

```
obsidian/seo-agent/
├── raw/
│   ├── competitors/
│   │   ├── domain1.com.md
│   │   └── domain2.com.md
│   └── keywords/
│       └── medical-keywords.md
│
├── wiki/
│   ├── index.md
│   ├── log.md
│   ├── concepts/
│   │   ├── seo-basics.md
│   │   └── medical-seo.md
│   ├── strategies/
│   │   ├── competitor-analysis.md
│   │   └── keyword-research.md
│   └── sources/
│       └── processed-data.md
│
└── decisions/
    └── 2026-05-05-keyword-strategy.md
```

---

**Примечания:**
- Добавь сюда свои скетчи и идеи
- Используй Excalidraw для визуальных диаграмм
- Этот файл — живой документ, обновляй его
