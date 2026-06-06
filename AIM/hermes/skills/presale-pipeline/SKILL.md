---
name: presale-pipeline
title: Presale Pipeline v3.6.0 — Autonomous Client Acquisition
description: >
  Полный автономный пайплайн пресейла: от первой ссылки до HTML-КП.
  Phase 0 (Deep Research) → Phase 1 (Tech Audit) → Phase 2 (Social + Competitors) →
  Phase 2.5 (Deep Scan) → Phase 2.6 (Closure Gate) → Phase 3 (Analyze) →
  Phase 4 (Hard Gate) → Phase 5 (HTML KP).
metadata:
  version: 3.6.0
  author: AIM
  depends_on:
    hermes_skills:
      deep-research-phase-0: ">=1.0"
      social-verifier: ">=1.0"
      content-analyzer: ">=1.0"
      competitor-scorer: ">=1.1"
      financial-fetcher: ">=1.1"
      html-kp-generator: ">=1.2"
      tech-auditor: ">=1.0"
      reel-scraper: ">=1.0"
---

# Presale Pipeline v3.6.0

Автономный пресейл-пайплайн. Получает на вход ссылку на сайт клиники → выдаёт HTML-КП.

**Принцип:** No-Stop Rule. Никаких остановок между фазами. Фазы идут непрерывно.

**Нумерация фаз (v3.6.0):**
- Phase 0 (NEW): Deep Research — mandatory pre-flight
- Phase 1 (was Phase 0): Init + Tech Audit
- Phase 2 (was Phase 1): Social + Competitors
- Phase 2.5 (was Phase 1.5): Deep Scan
- Phase 2.6 (was Phase 1.6): Closure Gate
- Phase 3 (was Phase 2): Analyze
- Phase 4 (was Phase 3): Hard Gate
- Phase 5 (was Phase 4): HTML KP

---

## Phase 0 — Deep Research (MANDATORY PRE-FLIGHT)

Перед ЛЮБЫМ техническим аудитом — выполнить deep research клиники и врачей. Это не опционально.

### 0.0 Запуск Deep Research

1. Загрузи deep-research-phase-0 skill: `skill_view(name='deep-research-phase-0')`
2. Выполни все 5 шагов согласно SKILL.md
3. Результаты автоматически запишутся в data.json["deep_research"]

### 0.1 Проверка результата

После выполнения — убедись что data.json содержит deep_research.clinic и deep_research.doctors.
Если нет — перезапусти Phase 0.

Проверка:
```bash
python3 -c "
import json
d = json.load(open('/root/work/presale/{client}/data.json'))
dr = d.get('deep_research', {})
print(f\"Clinic: {bool(dr.get('clinic'))}, Doctors: {len(dr.get('doctors', []))}\")
"
```

### 0.2 Быстрый доклад пользователю

После завершения Phase 0 — выведи короткую сводку (2-3 предложения):
- Количество найденных врачей, сколько «звёзд» (д.м.н., профессоров)
- Основные рейтинги клиники
- Продолжительность исследования

НЕ спрашивай разрешения продолжать — сразу переходи к Phase 1.

### 0.3 Переход к Phase 1

Автоматически, без паузы. Deep Research завершён → начинаем технический аудит.

---

## Phase 1 — Init + State Machine (was Phase 0)

### 1.0 Инициализация

1. Создать директорию: `/root/work/presale/{client}/`
2. Скопировать state template: `cp /root/work/presale/presale-state.template.json /root/work/presale/{client}/presale-state.json`
3. Определить домен из URL клиента

### 1.1 Технический аудит сайта

Загрузи tech-auditor skill: `skill_view(name='tech-auditor')`

Выполни полный технический аудит сайта клиента:
- PageSpeed (desktop + mobile)
- SSL-сертификат (срок действия, валидность)
- Технологический стек (CMS, фреймворки, хостинг)
- Мобильная адаптация
- Структура URL, мета-теги
- Скорость загрузки, размер страниц

Результаты → `data.json["clinic"]["tech_audit"]`

### 1.2 Финансовые данные

Загрузи финансовый модуль: `skill_view(name='financial-fetcher')`

Извлечь: ИНН, ОГРН, название юрлица, выручку, прибыль, сотрудников, лицензии.

Результаты → `data.json["clinic"]["inn"]`, `data.json["clinic"]["revenue"]`, etc.

### 1.3 Обновление state machine

После выполнения Phase 1:
- `phase1-site-audit` → completed
- `phase0-finance` → completed
- `phase` → 2

---

## Phase 2 — Social + Competitors (was Phase 1)

### 2.0 Social Verifier

Загрузи social-verifier skill: `skill_view(name='social-verifier')`

ВАЖНО: social-verifier получает pre-discovered social profiles из `data.json["deep_research"]["doctors"]`. Не ищет профили заново — только верифицирует найденное в Phase 0.

5-pass алгоритм верификации:
1. Instagram search + verification
2. VK search + verification
3. Telegram channel discovery
4. Cross-platform matching
5. Follower count validation

Результаты → `data.json["doctors"][].social_profiles`

### 2.1 Competitor Discovery

Загрузи competitor-scorer skill: `skill_view(name='competitor-scorer')`

Найти и проанализировать конкурентов:
- Поиск через поисковые системы + Apify
- Классификация по специализации
- Если deep_research содержит competitors[] из Phase 0 — дополнить, не дублировать

Результаты → `data.json["competitors"]`

### 2.2 Reels / Video Content

Загрузи reel-scraper skill: `skill_view(name='reel-scraper')`

Поиск reels/shorts/video-контента клиники и конкурентов.

### 2.3 Обновление state machine

- `phase1-social-audit` → completed
- `phase1-competitors` → completed
- `phase1-reels` → completed
- `phase` → 2.5

---

## Phase 2.5 — Deep Scan (was Phase 1.5)

Углублённое сканирование на основе собранных данных.

### 2.5.1 Дополнительный поиск

Для врачей с `research_confidence: SINGLE_SOURCE` или `LLM_INFERRED` — дополнительный поиск для повышения confidence.

### 2.5.2 Проверка конкурентов

Поверхностная проверка: все ли ключевые конкуренты найдены.

### 2.5.3 Обновление state machine

- `phase` → 2.6

---

## Phase 2.6 — Closure Gate (was Phase 1.6)

Проверка полноты данных перед анализом.

### 2.6.1 Запуск Closure Loop

Проверить все источники на наличие новых врачей, не учтённых ранее.
- Максимум 2 итерации Closure Loop
- При обнаружении новых врачей → вернуться к Phase 0 Steps 2-3

### 2.6.2 Запуск quality-gate.py

```bash
python3 /root/bin/quality-gate.py /root/work/presale/{client}/data.json
```

Если есть критические gaps — закрыть их перед переходом к Phase 3.

### 2.6.3 Обновление state machine

- `phase` → 3

---

## Phase 3 — Analyze (was Phase 2)

### 3.0 Content Analysis

Загрузи content-analyzer skill: `skill_view(name='content-analyzer')`

Анализ контента клиента:
- Контент-стратегия (блог, статьи, новости)
- Per-expert карточки (использует regalia из deep_research.doctors)
- Gap-анализ контента

Результаты → `data.json["content"]`

### 3.1 Обновление state machine

- `phase2-content-analysis` → completed
- `phase2-gap-audit` → completed
- `phase` → 4

---

## Phase 4 — Hard Gate (was Phase 3)

Финальная проверка всех данных перед генерацией КП.

### 4.0 Полная валидация data.json

```bash
python3 /root/bin/quality-gate.py /root/work/presale/{client}/data.json --strict
```

Все CRITICAL gaps должны быть закрыты. WARNING gaps допустимы.

### 4.1 Проверка deep_research completeness

Убедиться что:
- `deep_research.clinic` содержит историю и рейтинги
- `deep_research.doctors` не пуст
- Star-врачи имеют углублённое исследование

### 4.2 Обновление state machine

- `phase` → 5

---

## Phase 5 — HTML KP (was Phase 4)

### 5.0 Генерация коммерческого предложения

Загрузи html-kp-generator skill: `skill_view(name='html-kp-generator')`

Генерация 12-block HTML КП на основе data.json:
1. Обложка
2. О клинике (из deep_research.clinic)
3. Ключевые врачи (из deep_research.doctors — star + core)
4. Технический аудит
5. Социальные сети
6. Конкуренты
7. Контент-стратегия
8. Рекламная стратегия
9. SEO-рекомендации
10. Дорожная карта
11. Коммерческое предложение
12. Контакты

### 5.1 Обновление state machine

- `phase4-html-kp` → completed
- `phase` → complete

---

## Closure Loop Algorithm

На каждом этапе, где происходит поиск (Phase 0 Step 3, Phase 2, Phase 2.5):

1. Собрать все найденные сущности (врачи, конкуренты, соцсети)
2. Сравнить с уже учтёнными в data.json
3. Новые сущности → добавить в соответствующий раздел
4. Прогнать через соответствующий шаг исследования
5. Повторить максимум 2 раза

После 2 итераций — зафиксировать `closure_loop_truncated: true` и продолжить.

---

## No-Stop Rule

После инициализации (Phase 1.0) — пайплайн идёт непрерывно до Phase 5.

**Единственные допустимые остановки:**
- Пользователь явно сказал «стоп» или «хватит»
- Критическая ошибка (сайт не открывается, финансовые данные не найдены после 3 попыток)

**Не допустимы:**
- «Продолжаем?» между фазами
- «Нормально?» после каждого шага
- «Туда копаю?» во время исследования

---

## State Machine

Текущее состояние хранится в `/root/work/presale/{client}/presale-state.json`.

**Формат:**
```json
{
  "client": "short-name",
  "url": "https://clinic-domain.ru",
  "phase": 0,
  "step": "init",
  "completed": [],
  "pending": [
    "phase0-deep-research-extract-doctors",
    "phase0-deep-research-classify",
    "phase0-deep-research-doctors",
    "phase0-deep-research-clinic",
    "phase0-deep-research-merge",
    "phase0-site-audit",
    "phase0-finance",
    "phase1-social-audit",
    "phase1-competitors",
    "phase1-reels",
    "phase2-content-analysis",
    "phase2-gap-audit",
    "phase4-html-kp"
  ],
  "errors": [],
  "gaps": 0,
  "iterations": 0,
  "started_at": "",
  "updated_at": ""
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.6.0 | 2026-06-06 | Added Phase 0 (Deep Research). Renumbered phases. Updated depends_on with deep-research-phase-0 >=1.0 |
| 3.5.0 | 2026-05-31 | Added Phase 1.6 Closure Gate, quality-gate.py integration |
| 3.4.0 | 2026-05-25 | Added Reel Scraper (Phase 1) |
| 3.3.0 | 2026-05-20 | Added social-verifier 5-pass algorithm |
