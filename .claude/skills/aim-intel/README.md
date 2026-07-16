# Инструкция: ручная разведка конкурента → сервер AIM

Ты запускаешь разведку со своей машины (экономия токенов), я принимаю результат на сервере.

## 1. Структура на сервере

```
/root/projects/{client}/competitors/{slug}/
├── data.json       ← заливаешь сюда результат разведки
└── (profile.json)  ← не нужен, все в shared/competitors.json
```

- `{client}` — slug клиента (arclinic, detstvo-plus, ...)
- `{slug}` — slug конкурента (dega, rami, liks, ...)

## 2. Единый список конкурентов

Файл `/root/projects/{client}/shared/competitors.json` — массив:

```json
[
  {
    "id": "dega",
    "name": "DEGA Clinic",
    "instagram": "dega_clinic",
    "ig_followers": 40178,
    "threat": "🔴 КРИТИЧЕСКИЙ",
    "threat_why": "29 врачей, 873 отзыва на ПроДокторов, 5 платформ",
    "website": "",
    "telegram": "",
    "vk": "",
    "active": true,
    "monitoring": false,
    "intel_completed": false
  }
]
```

Если конкурента там ещё нет — добавь запись. `intel_completed` выставится автоматически, когда появится `data.json`.

## 3. Формат data.json (результат разведки)

ТА ЖЕ структура, что у клиента. Все поля обязательны. Если данных нет — пустой массив/ноль/пустая строка.

```json
{
  "slug": "dega",
  "client_slug": "arclinic",
  "mode": "competitor-intel",

  "clinic": {
    "name": "DEGA Clinic",
    "full_name": "DEGA Clinic — пластическая хирургия и косметология",
    "city": "Санкт-Петербург",
    "address": "Рабочий переулок, 3",
    "website": "https://dega.ru",
    "founded_year": null,
    "specialization": ["пластическая хирургия", "косметология", "стоматология"],
    "rating": {
      "yandex_maps": {"rating": 4.5, "reviews": 200},
      "prodoctorov": {"rating": 4.8, "reviews": 873},
      "2gis": {"rating": 4.3, "reviews": 150}
    },
    "legal": {
      "name": "ООО «...»",
      "inn": "78...",
      "revenue_2025": null,
      "revenue_growth": null
    },
    "social_media": {
      "instagram": {"handle": "dega_clinic", "followers": 40178, "posts": 3667, "er": null},
      "telegram": [],
      "vk": ""
    }
  },

  "doctors": [
    {
      "name": "Фамилия Имя Отчество",
      "tier": "core",
      "specialization": "Пластический хирург",
      "degree": "д.м.н.",
      "experience": 20,
      "instagram": "handle",
      "ig_followers": 5000
    }
  ],

  "content_analysis": {
    "clinic_ig": {
      "handle": "dega_clinic",
      "followers": 40178,
      "er": 0.8,
      "themes": ["до/после операций", "экспертный контент", "закулисье"],
      "format": "эксперт + визуальный",
      "top_post_likes": 500,
      "top_post_views": 10000,
      "gap": "Нет образовательного контента"
    }
  },

  "tech_audit": {
    "speed": {
      "performance": 70,
      "core_web_vitals": "Passed",
      "lcp_field": "2.0s"
    },
    "schema": "MedicalBusiness",
    "analytics": "Яндекс.Метрика"
  },

  "smi": [
    {"source": "РБК", "title": "...", "url": "https://...", "date": "2025"}
  ],

  "reviews_analysis": {
    "prodoctorov_rating": 4.8,
    "prodoctorov_count": 873,
    "positive_themes": ["...", "..."],
    "negative_themes": ["..."]
  },

  "gaps": ["описание разрыва с клиентом"],
  "wow_insights": ["ключевой инсайт для сравнения"]
}
```

**Правила заполнения:**
- Все строки — UTF-8
- Если данных нет — `null`, `[]`, `""`, `0`
- Не додумывать. `confidence: "LLM_INFERRED"` — честно
- Никаких длинных тире (—), только короткие (–)
- Термин «EGRUL» не использовать (→ «выписка ФНС»)

## 4. Промпт для LLM на твоей машине

```
Ты — агент конкурентной разведки AIM. Собери полные данные о конкуренте:

КЛИНИКА: {название}
ГОРОД: Санкт-Петербург
INSTAGRAM: @{handle}
САЙТ: {url}

Собери:
1. ВСЕХ врачей с сайта (ФИО + специализация + должность)
2. Рейтинги: Яндекс.Карты, ProDoctorov, 2ГИС
3. Instagram: подписчики, посты, ER, темы контента (3-5), формат, топ-пост
4. Технический аудит сайта: PageSpeed (pagespeed.web.dev), Schema.org, llms.txt
5. СМИ-упоминания (4 поиска: site:forbes.ru/rbc.ru/kommersant.ru, site:marieclaire.ru/vogue.ru, site:vademec.ru, региональные)
6. Выписка ФНС: ИНН, выручка (egrul.nalog.ru — 2 шага: POST с ИНН → токен → GET search-result/{token})
7. Ключевые враги: у кого из врачей есть Instagram, сколько подписчиков, темы контента

Верни результат СТРОГО в JSON-формате data.json (схема прилагается).
Файл сохрани как: /root/projects/arclinic/competitors/{slug}/data.json

БЕЗ длинных тире. БЕЗ «EGRUL» (→ «выписка ФНС»). БЕЗ додумывания.
Если данных нет — null или пустой массив.
```

## 5. Как залить результат на сервер

```bash
# Вариант А — scp
scp data.json root@<server>:/root/projects/arclinic/competitors/{slug}/data.json

# Вариант Б — отправить файл в Telegram боту
# Бот примет data.json и положит в нужную папку

# Вариант В — через shared-папку (если настроена)
cp data.json /mnt/aim/projects/arclinic/competitors/{slug}/data.json
```

После заливки — напиши мне в DM: «разведка {slug} залита». Я автоматически подхвачу.

## 6. Проверка результата

```bash
# На сервере:
python3 /root/bin/competitor-mgr.py list arclinic    # статус: ✅ = data.json есть
python3 /root/bin/competitor-mgr.py compare arclinic  # сравнение клиента с конкурентами
```
