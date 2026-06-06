---
name: deep-research-phase-0
title: Deep Research Phase 0 — Mandatory Pre-Flight Intelligence
description: >
  Обязательный deep research клиники и ключевых врачей ПЕРЕД основным пресейл-пайплайном.
  Автоматическое определение «звёзд» (д.м.н., профессора, авторы методик) с углублённым
  исследованием. Конкуренты — только поверхностный анализ. Результаты → data.json["deep_research"].
metadata:
  version: 1.0.0
  author: AIM
  phase: 0
  position: before-presale-phase-1
  depends_on:
    - Hermes tools: web_search, web_extract, browser_navigate, browser_console, file_read, file_write
    - Server tools: /root/bin/deep-research-merge.py, /root/bin/fc (Firecrawl CLI)
    - Hermes skills: financial-fetcher (for legal entity + licenses)
  complements:
    - social-verifier (Phase 0 discovers candidate profiles → social-verifier validates them)
    - content-analyzer (Phase 0 provides doctor regalia → content-analyzer builds expert cards)
    - html-kp-generator (Phase 0 provides clinic history + key doctors → KP blocks)
---

# Deep Research Phase 0 — Mandatory Pre-Flight Intelligence

## Purpose

Каждый пресейл начинается с глубокого изучения самой клиники и её врачей. Без этого маркетинговый смысл КП теряется — мы не знаем, КТО работает в клинике. «Заслуженные» доктора (д.м.н., профессора, авторы методик) — главный актив, который система должна распознавать автоматически.

**Когда запускать:** Перед ЛЮБЫМ техническим аудитом сайта. Это не опционально. Phase 0 → Phase 1 → Phase 2 → ... → HTML КП.

**Результат:** `data.json["deep_research"]` с полными данными о клинике и врачах.

---

## Iron Rule 1 — No Confirmation Gates

Phase 0 работает полностью автономно. Никаких остановок, никаких подтверждений.

**Правила:**
- Нашёл врача на сайте → исследуй немедленно. НЕ спрашивай «исследовать этого врача?». Ответ всегда ДА.
- Нашёл д.м.н. или профессора → углублённое исследование автоматически. НЕ спрашивай «углублённо исследовать?».
- Все врачи на странице `/specialisty` или `/vrachi` — fair game для исследования.
- Единственная остановка: пользователь сказал «стоп» или «хватит».
- Принцип «no interruption»: никаких «нормально?», «продолжаем?», «туда копаю?» посреди процесса.

**Почему:** Каждый вопрос-подтверждение ломает поток глубокого исследования. Клиент уже дал ссылку — этого достаточно. Все врачи на сайте — наша зона ответственности.

---

## Iron Rule 2 — JSON Handling

НИКОГДА не пиши JSON в data.json напрямую через `file_write`. Всегда используй Python-хелпер.

**Правило:**
```bash
# Подготовь JSON с результатами глубокого исследования и передай через stdin:
echo '{"clinic": {...}, "doctors": [...]}' | python3 /root/bin/deep-research-merge.py {client}
```

**Почему:** Прямая запись JSON через LLM даёт ~7% ошибок (hallucinated keys, corrupted nesting, missing required fields). Python-хелпер валидирует структуру, классифицирует врачей и пишет атомарно (tempfile + rename).

**Для classify-only режима:**
```bash
python3 /root/bin/deep-research-merge.py {client} --classify-only
```
В этом режиме merge.py читает doctors[] из stdin и возвращает классифицированных врачей с полями tier, degrees, auto_flagged_star. Используется в Step 2 после извлечения врачей с сайта.

---

## Iron Rule 3 — Competitor Boundary

Phase 0 делает ТОЛЬКО поверхностный анализ конкурентов. Это жёсткая граница.

**В Phase 0 разрешено:**
- Название конкурента, сайт, специализация, примерная выручка
- Упоминание конкурента в рейтингах (prodoctorov, 2gis) — как контекст для оценки клиники

**В Phase 0 ЗАПРЕЩЕНО:**
- Анализ контента конкурентов
- Анализ соцсетей конкурентов (Instagram, VK)
- SEO-аудит конкурентов
- Поиск viral posts или рекламных кампаний конкурентов
- Любой deep-анализ конкурирующих клиник

**Маркер в data.json:** Все результаты по конкурентам помечаются `"competitor_depth": "surface-only"`.

**Deep-анализ конкурентов:** ИСКЛЮЧИТЕЛЬНО постконтрактная фаза. В КП честно указываем: «Это поверхностный анализ конкурентов. Детальный конкурентный анализ — после подписания договора.»

---

## Step 1 — Extract Doctors from Website

Извлечь полный список врачей с сайта клиники.

### 1.1 Основной метод: web_extract
```
web_extract(url=https://{clinic_domain}/specialisty)
web_extract(url=https://{clinic_domain}/vrachi)
web_extract(url=https://{clinic_domain}/doctors)
```
Пробуй все три пути. Обычно один из них содержит полный список.

### 1.2 Fallback 1: browser_console для Bitrix SPA
Если `web_extract` вернул пустой результат или 404 — сайт на Bitrix с SPA-роутингом.
```
browser_navigate(url=https://{clinic_domain})
browser_console: найти меню «Специалисты» или «Врачи» → клик → дождаться загрузки карточек → извлечь HTML карточек врачей
```

### 1.3 Fallback 2: google-indexed search
Если оба метода не дали результатов:
```
web_search site:{clinic_domain} врач OR специалист
```
Извлечь ФИО врачей из сниппетов поисковой выдачи.

### Данные для каждого врача
Для каждого найденного врача извлечь:
- **ФИО** (обязательно)
- **Специализация** (если указана на сайте)
- **Должность** (главный врач, руководитель отделения, etc.)
- **Опыт работы в годах** (если указан: «стаж 24 года» → experience_years=24)
- **Фото URL** (если доступно)
- **Описание/био** (текст карточки врача целиком — для классификации в Step 2)

---

## Step 2 — Classify Doctors into Tiers

Классифицировать каждого врача на tier: star, core, или team.

### 2.1 Подготовка данных
Для каждого врача собрать bio_string из всех источников:
- Должность со страницы врача
- Текст карточки врача
- Специализация
- Любые регалии, упомянутые на сайте

Оценить experience_years:
- Если явно указан стаж → использовать это число
- Если указан год начала практики → `текущий_год - год_начала`
- Если нет данных → 0 (классификация будет только по тексту)

### 2.2 Классификация через Python helper
```bash
echo '{"doctors": [{"full_name": "ФИО", "bio": "собранный bio_string", "experience_years": 24}]}' | \
  python3 /root/bin/deep-research-merge.py {client} --classify-only
```

### 2.3 Tier definitions

| Tier | Критерии | Глубина исследования |
|------|---------|---------------------|
| **star** | д.м.н., профессор, заслуженный врач РФ, академик РАМН, член-корр. РАН, автор методик/монографий, организатор конгрессов, главный окружной/городской специалист, стаж 25+ лет при core | 7-10 поисков + Firecrawl deep research |
| **core** | к.м.н., главный врач, руководитель отделения, зав. отделением, доцент, стаж 15+ лет | 5 поисков |
| **team** | Все остальные врачи | 2-3 поиска |

### 2.4 auto_flagged_star
Поле `auto_flagged_star=true` когда star присвоен через qualifier (автор методик, организатор конгрессов) или experience heuristic (25+ лет), а НЕ через формальную степень (д.м.н., профессор). Это важно: такие врачи — «скрытые звёзды», которых система нашла сама.

---

## Step 3 — Deep Research per Doctor (tier-dependent)

Для каждого врача выполнить мультипроходной поиск. Глубина зависит от tier.

### 3.1 Для ВСЕХ врачей (Tier 1 + 2 + 3)

**prodoctorov.ru (рейтинг и отзывы):**
```
web_search site:prodoctorov.ru "ФИО врача"
```
ВНИМАНИЕ: НЕ использовать web_extract на prodoctorov.ru — Cloudflare защита. Только web_search. Из google-сниппетов извлечь: рейтинг, количество отзывов, стаж (если видно).

**docdoc.ru (отзывы, цены приёма):**
```
web_search site:docdoc.ru "ФИО врача"
```

**Instagram (поиск профиля):**
```
web_search site:instagram.com "ФИО врача" {город} {специализация} {клиника}
```
ВАЖНО: Всегда включать город + специализацию + название клиники. Без этого — ложные срабатывания на однофамильцев.

**VK (поиск профиля):**
```
web_search site:vk.com "ФИО врача" {клиника}
```

### 3.2 Дополнительно для Tier 1 + 2

**eLibrary.ru (научные публикации):**
```
web_search site:elibrary.ru "ФИО автора"
```
Извлечь: количество публикаций, индекс цитирования (если доступно).

**dissercat.com (диссертации):**
```
web_search site:dissercat.com "ФИО"
```
Найти диссертацию: год защиты, специальность, шифр специальности.

**СМИ-упоминания:**
```
web_search "ФИО врача" интервью OR эксперт OR награда -site:{clinic_domain}
```

### 3.3 Только для Tier 1 (Firecrawl Deep Research)
```
fc deep-research "ФИО врача {специализация} научные публикации конгрессы награды"
```
Firecrawl сделает многошаговый deep research с перекрёстной проверкой источников (10-15 источников). Это самая ресурсоёмкая операция — только для звёзд.

### 3.4 Формат результатов per doctor
```json
{
  "full_name": "Круглик Сергей Викторович",
  "tier": "star",
  "experience_years": 24,
  "degrees": ["к.м.н."],
  "roles": ["Руководитель клиники", "Пластический хирург"],
  "publications_count": 15,
  "dissertation": {
    "title": "Хирургическая коррекция...",
    "year": 2005,
    "specialty": "14.01.17 — Хирургия"
  },
  "patient_reviews_rating": 4.8,
  "patient_reviews_count": 45,
  "social_profiles": {
    "instagram": {"username": "drkruglik", "followers": "16 600"},
    "vk": {"url": "https://vk.com/...", "followers": "22 400"},
    "telegram": ["@drkruglik", "@drkruglik_results"]
  },
  "media_mentions": [
    {"source": "РБК Стиль", "title": "...", "url": "...", "date": "2025-03-15"},
    {"source": "Шоу Собчак", "title": "Красота требует КЭШ", "url": "...", "date": "2024-09-01"}
  ],
  "conferences": ["ISAM Moscow 2025", "Балтийский конгресс 2024"],
  "auto_flagged_star": false,
  "research_confidence": "VERIFIED"
}
```

### 3.5 Параллельный pre-discovery для social-verifier
Попутно с исследованием врачей собрать candidate social profiles (Instagram username, VK URL, Telegram username). Эти данные НЕ верифицируются в Phase 0 — они передаются social-verifier в Phase 2 для 5-pass валидации. Но discovery здесь, чтобы social-verifier не искал заново.

---

## Step 4 — Clinic Deep Research

Глубокое исследование самой клиники: история, репутация, юридическое лицо, лицензии.

### 4.1 История клиники
```
web_search "{название клиники}" история основана
web_search "{название клиники}" {город} год основания
```
Извлечь: founded_year, founders (если доступно), основные вехи развития.

### 4.2 Рейтинги на всех платформах (parallel)
```
web_search site:prodoctorov.ru "{название клиники}"
web_search site:docdoc.ru "{название клиники}"
web_search site:2gis.ru "{название клиники}"
web_search "{название клиники}" yandex maps рейтинг
```
Для каждой платформы извлечь: рейтинг (звёзды/баллы), количество отзывов, URL страницы клиники.

### 4.3 Юридическое лицо и лицензии
Делегировать в financial-fetcher skill:
```
skill_view(name='financial-fetcher')
```
financial-fetcher извлечёт: ИНН, ОГРН, название юрлица, дату регистрации, выручку, прибыль, сотрудников, лицензии (из roszdravnadzor).

### 4.4 СМИ-упоминания
```
web_search "{название клиники}" рейтинг OR награда OR статья -site:{clinic_domain}
```
Исключить сайт самой клиники (результаты только из независимых источников).

### 4.5 Конкуренты (только поверхностно, per Iron Rule 3)
```
web_search "{специализация} {город} рейтинг клиник"
web_search site:prodoctorov.ru "{специализация}" {город}
```
Для каждого найденного конкурента зафиксировать:
- Название
- Сайт
- Специализация
- Примерная выручка (из financial-fetcher, если доступно)

**НЕ углубляться** в соцсети, SEO, контент конкурентов. Только факты, видимые из рейтинговых платформ и поисковых сниппетов.

В data.json добавить маркер: `"competitor_depth": "surface-only"`.

### 4.6 Формат clinic данных
```json
{
  "clinic": {
    "history": "Основана в 2008 году пластическим хирургом Кругликом С.В....",
    "founded_year": 2008,
    "founders": ["Круглик Сергей Викторович"],
    "reputation": {
      "prodoctorov_rating": 5.0,
      "prodoctorov_reviews": 301,
      "docdoc_rating": 4.7,
      "docdoc_reviews": 85,
      "yandex_maps_rating": 4.9,
      "two_gis_rating": 4.8
    },
    "ratings": {
      "prodoctorov": {"rating": 5.0, "reviews": 301, "url": "https://prodoctorov.ru/..."},
      "docdoc": {"rating": 4.7, "reviews": 85, "url": "https://docdoc.ru/..."},
      "yandex_maps": {"rating": 4.9, "reviews": 120, "url": "https://yandex.ru/maps/..."},
      "2gis": {"rating": 4.8, "reviews": 95, "url": "https://2gis.ru/..."}
    },
    "legal_entity": {
      "name": "ООО «НОВАЯ МЕДИЦИНА»",
      "inn": "7703396052",
      "ogrn": "1157746792268",
      "registration_date": "2015-09-01"
    },
    "media_mentions": [
      {"source": "РБК Стиль", "title": "...", "url": "...", "date": "2025-03-15"}
    ],
    "licenses": [
      {"number": "ЛО-77-01-XXXXXX", "date": "2023-01-15", "services": ["..."], "_source": "roszdravnadzor.gov.ru"}
    ],
    "competitors": [
      {"name": "...", "url": "...", "specialty": "...", "estimated_revenue": "..."}
    ],
    "competitor_depth": "surface-only"
  }
}
```

---

## Step 5 — Merge into data.json

Собрать все результаты исследований в JSON формата `deep_research` и передать в Python-хелпер:

```bash
echo '{
  "clinic": {...},
  "doctors": [...],
  "_meta": {
    "sources_used": ["prodoctorov.ru", "docdoc.ru", "elibrary.ru", "checko.ru", "web_search"],
    "research_duration_seconds": 340
  }
}' | python3 /root/bin/deep-research-merge.py {client}
```

Хелпер автоматически:
- Классифицирует врачей (если ещё не классифицированы)
- Добавляет `_meta` с researched_at, tier counts, sources_used
- Мержит в `data.json["deep_research"]`, сохраняя все существующие поля (clinic.inn, clinic.revenue, etc.)
- Пишет атомарно (tempfile + os.rename)

**Проверка результата:**
```bash
python3 -c "import json; d=json.load(open('/root/work/presale/{client}/data.json')); print('clinic:', bool(d.get('deep_research',{}).get('clinic')), 'doctors:', len(d.get('deep_research',{}).get('doctors',[])))"
```

---

## Closure Loop

Если во время Step 3 обнаружен новый врач, не указанный на сайте клиники (например, на prodoctorov.ru в списке врачей клиники или через СМИ-упоминания) — добавить его в doctors[] и прогнать через:

1. **Step 2** — классификация (classify-only режим)
2. **Step 3** — tier-appropriate deep research

Максимум 2 итерации Closure Loop. Если на итерации 2 обнаружены новые врачи — зафиксировать их в `_meta.closure_loop_truncated: true` и НЕ запускать третью итерацию (предотвращение бесконечного расширения скоупа).

---

## Confidence Markers

Каждый finding в deep_research должен быть промаркирован уровнем достоверности:

| Маркер | Значение | Когда использовать |
|--------|---------|-------------------|
| `VERIFIED` | Подтверждено из 2+ независимых источников | Рейтинг врача подтверждён и на prodoctorov, и на docdoc; публикация найдена и на elibrary, и в СМИ |
| `SINGLE_SOURCE` | Один источник, требует валидации | Instagram найден через web_search, но не верифицирован; рейтинг только на одной платформе |
| `LLM_INFERRED` | Вывод сделан LLM, может быть неточным | Стаж оценён по контексту («молодой специалист», «ведущий эксперт»); год основания клиники предположен по косвенным упоминаниям |

**Формат:**
- Для полей врача: `"research_confidence": "VERIFIED"`
- Для отдельных claims: `"experience_years_source": "LLM_INFERRED: based on 'ведущий специалист с многолетним стажем'"`

---

## Output Data Contract

После выполнения всех шагов `data.json["deep_research"]` содержит:

```json
{
  "deep_research": {
    "clinic": {
      "history": "string",
      "founded_year": 2008,
      "reputation": {"prodoctorov_rating": 5.0, ...},
      "ratings": {...},
      "legal_entity": {"inn": "...", "ogrn": "...", ...},
      "media_mentions": [...],
      "licenses": [...],
      "competitors": [...],
      "competitor_depth": "surface-only"
    },
    "doctors": [
      {
        "full_name": "string (required)",
        "tier": "star|core|team",
        "experience_years": 24,
        "degrees": ["к.м.н."],
        "roles": ["Пластический хирург"],
        "publications_count": 15,
        "dissertation": {...},
        "patient_reviews_rating": 4.8,
        "patient_reviews_count": 45,
        "social_profiles": {...},
        "media_mentions": [...],
        "conferences": [...],
        "auto_flagged_star": false,
        "research_confidence": "VERIFIED|SINGLE_SOURCE|LLM_INFERRED"
      }
    ],
    "_meta": {
      "researched_at": "2026-06-06T10:00:00Z",
      "total_doctors_found": 42,
      "star_doctors": 1,
      "core_doctors": 3,
      "team_doctors": 38,
      "sources_used": ["prodoctorov.ru", "docdoc.ru", "elibrary.ru", "checko.ru", "web_search"],
      "research_duration_seconds": 340
    }
  }
}
```

---

## Downstream Consumers

Результаты Phase 0 используются:

- **social-verifier (Phase 2):** Получает pre-discovered candidate social profiles (Instagram username, VK URL, Telegram username). Не ищет профили заново — только верифицирует найденное.
- **content-analyzer (Phase 3):** Получает регалии врачей (degrees, publications, conferences) для построения per-expert карточек в контент-стратегии.
- **html-kp-generator (Phase 5):** Получает блок «О клинике» (история, founded_year, рейтинги, лицензии) и блок «Ключевые врачи» (star + core врачи с регалиями).

---

## Error Handling

| Ситуация | Действие |
|---------|---------|
| Сайт клиники не открывается | Использовать Fallback 2 (google-indexed search) и данные из финансовых источников |
| 0 врачей найдено на сайте | Зафиксировать `total_doctors_found: 0` в `_meta`, продолжить с clinic research |
| prodoctorov.ru заблокировал запрос | Использовать web_search (не web_extract), google-сниппеты |
| elibrary.ru недоступен | Пропустить, зафиксировать в `_meta.missing_sources: ["elibrary.ru"]` |
| financial-fetcher не нашёл ИНН | Попробовать альтернативные домены (checko.ru, rusprofile.ru) через web_search |
| deep-research-merge.py вернул ошибку | Проверить формат JSON, исправить, повторить. НЕ писать JSON напрямую. |

---

## Execution Time Budget

| Шаг | Tier 1 врачей | Tier 2 врачей | Tier 3 врачей | Типичная клиника (2★ + 3● + 35○) |
|-----|--------------|--------------|--------------|----------------------------------|
| Step 1: Extract | — | — | — | 30-60s |
| Step 2: Classify | — | — | — | 5-10s |
| Step 3: Per-doctor | 7-10 searches (60-90s) | 5 searches (30-45s) | 2-3 searches (15-20s) | 2×75s + 3×38s + 35×18s = ~15 min |
| Step 4: Clinic | — | — | — | 3-5 min |
| Step 5: Merge | — | — | — | 2-5s |
| **Total** | | | | **~20-25 минут** |

При параллельном запуске Phase 1 (технический аудит) во время Step 3 для Tier 1 врачей — общее время пайплайна не увеличивается.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-06-06 | Initial release: 3 Iron Rules, 5 Steps, Tier 1/2/3 classification, Closure Loop, Confidence Markers |
