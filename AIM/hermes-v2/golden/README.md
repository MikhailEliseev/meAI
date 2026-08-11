# Golden-тесты качества ответов чата AIM

Измеримый базис **качества ответа** (не «работает/упало»). Фиксирует текущее
состояние **до починки** и валидирует каждый фикс P0 перезапуском.

## Что проверяют (чеки)

| ID | Чек | Что ловит | Дефект |
|----|-----|-----------|--------|
| **G1** | Grounding — каждая цифра/сущность в ответе LLM есть в данных | LLM выдумывает цифры | **P0-1** (главный) |
| **G2** | Structure — секции Позиция/Сильные/Рост/Отзывы/Рекомендации | игнор спецификации | поведение LLM |
| **G3** | Clean — нет сырого JSON, `4.3000…`, `:::`, утечек `[SUGGESTIONS]`, «трафик», Instagram-рек | симптомы из коммитов + 148-ФЗ | **P1** |
| **G4** | Data completeness — тулы вернули непустые данные | каскад мусора из Perplexity/ФНС | **P1** |
| **G5** | Coherence — нет противоречий (лидер vs отстаём) | противоречивые промпты | **P0-2** |
| **JUDGE** | LLM-as-judge — рубрика 0-5 | сводный качественный скор | — |

## Запуск

Тесты исполняются **внутри контейнера** `aim-hermes-v2` (все ключи в env).
Файлы — source-of-truth в репо (`AIM/hermes-v2/golden/`), синхронизируются на сервер.

### С локальной машины (одна команда):

```bash
# 1. Залить на сервер (в зеркало исходников)
scp -r AIM/hermes-v2/golden aim:/opt/aim/AIM/hermes-v2/

# 2. Скопировать в контейнер
ssh aim 'docker cp /opt/aim/AIM/hermes-v2/golden aim-hermes-v2:/opt/hermes-v2/golden'

# 3. Прогнать refresh (реальные API → snapshot). Результаты в /opt/data/golden (примонтировано)
ssh aim 'docker exec -w /opt/hermes-v2 aim-hermes-v2 python3 golden/run_golden.py --refresh --out /opt/data/golden'

# 4. Подтянуть результаты обратно
scp -r aim:/opt/hermes-v2-data/golden ./golden-results
```

### Режимы

```bash
# Реальный прогон всех кейсов + LLM-judge (медленно, ~токены)
python3 golden/run_golden.py --refresh --judge

# Один кейс
python3 golden/run_golden.py --refresh --case dentakrd

# Проверить существующие snapshot (быстро, бесплатно — без вызова API)
python3 golden/run_golden.py
```

## Переменные окружения

| Переменная | По умолчанию | Что делает |
|------------|--------------|------------|
| `GOLDEN_SKIP_PUBLISH` | `1` | Не публиковать отчёт в WordPress (monkeypatch `_auto_publish_report`). Код отчёта всё равно отработает. |
| `GOLDEN_OUT` | `./cases` | Куда писать snapshot/transcript. В контейнере: `/opt/data/golden` |

## Структура вывода

```
cases/{case_id}/
├── snapshot.json   # снимок событий: tool_calls, formatted_blocks, llm_text, checks, judge
└── transcript.md   # читаемый транскрипт — данные + ответ LLM (для глаз)
```

## Как читать scorecard

```
CASE            G1 ground  G2 struct  G3 clean  G4 data  G5 coh  JUDGE
implantkrd       8% ❌      4/5 ⚠️    FAIL ❌   3/3 ✅   ✅      1.8
...
AVG              10%                  0/5               ✅      1.9
```

- **G1 < 30%** → LLM не опирается на данные (P0-1 подтверждён численно).
- **G3 0/N pass** → сырой JSON/float-артефакты утекают в ответы (P1 подтверждён).
- После фикса P0-1 (передать данные в контекст LLM) **G1 должен прыгнуть к 70-90%**.

## Дизайн-решения

- **Pure stdlib** (нет pytest/pyyaml в контейнере): только `json, re, asyncio, argparse`.
- **Snapshot-паттерн**: дорогой прогон (`--refresh`) → дешёвые проверки (без флага) на snapshot.
- **Без HTTP/SSE**: вызываем `chat_with_tools(history)` напрямую, собираем события.
- **Monkeypatch вместо правки кода**: публикация отключается из harness, `llm.py` не трогается.

## Что НЕ делают

- Не чинят дефекты (отдельная фаза, валидируется перезапуском).
- Не заменяют 325 unit-тестов (те тестируют трубы, эти — качество ответа).
