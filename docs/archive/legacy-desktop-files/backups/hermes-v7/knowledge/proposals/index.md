# proposals/ — База коммерческих предложений

## Структура

```
proposals/
├── TEMPLATE.md          # Шаблон для новых КП
├── index.md             # Каталог всех КП
└── [client-slug]/       # Папка клиента
    ├── proposal.html    # Итоговый HTML-файл КП
    ├── feedback.md      # Обратная связь и правки
    └── outcome.md       # Итог: взял/не взял, уроки
```

## Каталог КП

| # | Клиент | Отрасль | Дата | Цена | Статус |
|---|--------|---------|------|------|--------|
| 1 | [psyholog48](psyholog48/) | Психология | 2026-06-03 | 80 000 ₽/мес | Ожидается |

## Статистика

- Всего КП: 1
- Принято: 0
- Отказано: 0
- Ожидается: 1
- Средняя цена: 80 000 ₽/мес
- Конверсия: n/a

## Конвейер качества

**[QUALITY.md](QUALITY.md)** — полный конвейер качества КП:
- Этап 0: Pre-CP Checklist (5 вопросов перед стартом)
- Этап 1: Zero-Trust Data Policy (ни одной цифры без источника)
- Этап 2: Структура (жёсткий порядок блоков + Cost of Inaction)
- Этап 3: Humanization Pipeline (Client-as-Hero + Linter)
- Этап 4: Trust Check (откуда я это знаю?)
- Этап 5: Pre-Send Quality Gate (CP Quality Score ≥ 0.80)
- Этап 6: Post-Send (follow-up + in-session learning)
