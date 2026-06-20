#!/usr/bin/env python3
"""Phase 1 COMPETITORS — iphk.ru.
Вызывает AIM API: find_competitors → run_ci_analysis → LLM-интерпретация.
Сохраняет сырые данные в проект.
"""
import json, os, sys, time
from datetime import datetime
from openai import OpenAI
import httpx

PROJECT = "/opt/data/projects/iphk.ru"
RAW = os.path.join(PROJECT, "raw-data")
os.makedirs(RAW, exist_ok=True)

AIM_API = os.getenv("AIM_API_BASE", "http://aim-app:8000")
LLM_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_KEY = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
if not LLM_KEY:
    raise RuntimeError("No LLM API key in env")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

CLIENT_URL = "https://iphk.ru"
CLIENT_NAME = "Институт пластической хирургии и косметологии"
CLIENT_CITY = "Москва"
CLIENT_SPEC = "пластическая хирургия и косметология"

# Конкуренты из Phase 0 Perplexity (имена + URL)
NAMED_COMPETITORS = [
    "СМ-Клиника smclinic.ru",
    "Клиника профессора Блохина blokhinclinic.ru",
    "Клиника доктора Бородина dr-borodin.ru",
    "Клиника Медицина medicina.ru",
    "Клиника доктора Корнеева korneevclinic.ru",
    "КЭМ kemclinic.ru",
    "Клиника доктора Шихова shikhovclinic.ru",
]

print(f"[{datetime.now().isoformat()}] Phase 1: COMPETITORS for {CLIENT_URL}")
print(f"  AIM API: {AIM_API}")

# ══════════════════════════════════════════════════════════════
# STEP 1: find_competitors
# ══════════════════════════════════════════════════════════════
print("\n── Step 1: find_competitors ──")
t0 = time.time()

async def step1():
    async with httpx.AsyncClient(timeout=600.0) as client:
        resp = await client.post(
            f"{AIM_API}/api/competitors/find",
            json={
                "url": CLIENT_URL,
                "count": 5,
                "named_competitors": NAMED_COMPETITORS,
            },
        )
        resp.raise_for_status()
        return resp.json()

import asyncio
data = asyncio.run(step1())
elapsed = time.time() - t0
print(f"  Done in {elapsed:.0f}s. success={data.get('success')}, competitors={len(data.get('competitors',[]))}")

# Сохраняем сырой ответ find_competitors
path_fc = os.path.join(RAW, "phase-1-find-competitors-raw.json")
with open(path_fc, "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"  Saved: {path_fc}")

if not data.get("success"):
    print(f"  ERROR: {data.get('error')}", file=sys.stderr)
    sys.exit(1)

competitors = data.get("competitors", [])
if not competitors:
    print("  ERROR: no competitors found", file=sys.stderr)
    sys.exit(1)

# Compact для run_ci_analysis (только то, что нужно)
ci_competitors = []
for c in competitors:
    ci_competitors.append({
        "brand_name": c.get("brand_name") or c.get("legal_name", "Конкурент"),
        "legal_name": c.get("legal_name", ""),
        "website": c.get("website", ""),
        "rating": c.get("rating"),
        "reviews_count": c.get("reviews_count"),
        "revenue_year": c.get("revenue_year"),
        "revenue_trend": c.get("revenue_trend"),
        "employee_count": c.get("employee_count"),
        "social_links": c.get("social_links", {}),
        "services": c.get("services", []),
    })

print(f"  Competitors for CI: {len(ci_competitors)}")

# ══════════════════════════════════════════════════════════════
# STEP 2: run_ci_analysis
# ══════════════════════════════════════════════════════════════
print("\n── Step 2: run_ci_analysis ──")
t0 = time.time()

async def step2():
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            f"{AIM_API}/api/competitors/analyze",
            json={
                "url": CLIENT_URL,
                "specialization": CLIENT_SPEC,
                "city": CLIENT_CITY,
                "services": [],
                "competitors": ci_competitors,
                "tier": "quick",
            },
        )
        resp.raise_for_status()
        return resp.json()

ci_data = asyncio.run(step2())
elapsed = time.time() - t0
print(f"  Done in {elapsed:.0f}s. has_chat_summary={bool(ci_data.get('chat_summary'))}")

# Сохраняем сырой ответ CI
path_ci = os.path.join(RAW, "phase-1-ci-analysis-raw.json")
with open(path_ci, "w") as f:
    json.dump(ci_data, f, ensure_ascii=False, indent=2)
print(f"  Saved: {path_ci}")

# ══════════════════════════════════════════════════════════════
# STEP 3: LLM Interpretation
# ══════════════════════════════════════════════════════════════
print("\n── Step 3: LLM Interpretation ──")

# Формируем конкурентные данные как это делает engine._interpret_phase
competitor_details = ci_data.get("competitor_details", [])
chat_summary = ci_data.get("chat_summary", "")
feature_matrix = ci_data.get("feature_matrix", {})
top_rec = ci_data.get("top_recommendation", "")
tactics = ci_data.get("steal_worthy_tactics", [])

# Строим текстовое представление данных
parts = []
parts.append("### find_competitors")
for i, c in enumerate(competitors, 1):
    parts.append(
        f"{i}. {c.get('brand_name') or c.get('legal_name', '?')} "
        f"({c.get('website', 'нет сайта')}) — "
        f"выручка {c.get('revenue_year') or 'нет данных'}, "
        f"тренд: {c.get('revenue_trend') or 'нет данных'}, "
        f"рейтинг {c.get('rating') or '—'}, "
        f"{c.get('reviews_count') or 0}+ отзывов"
    )

parts.append("\n### run_ci_analysis")
parts.append(f"competitor_details:")
for cd in competitor_details:
    rev = cd.get("revenue")
    if rev:
        rev_str = f"{rev:,.0f}".replace(",", " ")
        rev_str = f"revenue={rev_str}"
    else:
        rev_str = "revenue=null"
    parts.append(
        f"- {cd.get('name', '?')}: {rev_str}, "
        f"revenue_trend={cd.get('revenue_trend') or 'null'}, "
        f"seo_score={cd.get('seo_score')}, "
        f"gm_rating={cd.get('gm_rating')}"
    )

parts.append(f"\nchat_summary: {chat_summary[:500] if chat_summary else 'Нет данных'}")

if feature_matrix:
    parts.append(f"\nfeature_matrix:")
    fm_list = feature_matrix.get("competitors", []) if isinstance(feature_matrix, dict) else []
    for fm in fm_list:
        parts.append(
            f"- {fm.get('name', '?')}: "
            f"seo_score={fm.get('seo_score')}, "
            f"online_booking={fm.get('online_booking')}"
        )

tactics_str = "; ".join(tactics[:5]) if tactics else "нет"
parts.append(f"\nsteal_worthy_tactics: {len(tactics)} тактик — {tactics_str[:300]}")
parts.append(f"\ntop_recommendation: {top_rec[:300] if top_rec else 'Нет'}")

tool_output = "\n".join(parts)

# Теперь — interpretation_prompt из phases.py
INTERPRET_PROMPT = f"""Ты — старший аналитик агентства AIM. Твоя задача — построить СТРУКТУРИРОВАННЫЙ конкурентный анализ на основе данных, собранных инструментами find_competitors и run_ci_analysis.

Данные, которые ты получишь:
- competitor_details (список конкурентов с полями: name, url, revenue, revenue_trend, doctors_count, instagram_subscribers, instagram_username, seo_score, gm_rating, gm_reviews_count)
- chat_summary (текстовый анализ из CI)
- feature_matrix (сравнение фич)

## ФОРМАТ ОТВЕТА (СТРОГО):

### 1. Сравнительная таблица
Markdown-таблица с колонками:
| Конкурент | Выручка | Тренд | Врачей | Instagram | SEO |
|-----------|---------|-------|--------|-----------|-----|

Правила заполнения:
- **Первая строка — КЛИЕНТ**, имя жирным (**Клиника X**)
- Выручка: «4.3 млрд ₽», «742 млн ₽», «12.5 млн ₽» — форматируй читаемо
- Тренд: «↑ Растущий (+79%)», «→ Стабильный», «↓ Падение (-15%)», «—»
- Врачей: число из doctors_count, «—» если нет
- Instagram: «@username (~587K)», «27K», «Нет» если нет username
- SEO: «85/100», «—» если нет
- Если данных нет — «—»

### 2. Главный вывод
> BLOCKQUOTE (1-2 предложения). Главный стратегический инсайт: где находится клиент относительно рынка, какая ключевая возможность или угроза.

### 3. Сильные стороны клиента
2-3 пункта, каждый с конкретным фактом (цифра из competitor_details):
- Что у клиента лучше конкурентов? Где он уже выигрывает?

### 4. Точки роста
2-3 пункта, каждый с конкретным ориентиром (цифра конкурента-лидера):
- Где клиент отстаёт? Что нужно догонять?

**ВАЖНО:** Не выдумывай цифры. Если данных нет — честно пиши «—». Используй ТОЛЬКО данные из competitor_details.

КОНТЕКСТ ОТ PERPLEXITY (рынок, тренды):
Рынок пластической хирургии в Москве высококонкурентный. ИПХиК — один из старейших институтов (основан в 1959). Ключевые тренды: рост спроса на малоинвазивные процедуры, digital-маркетинг, видеоконтент. Пациенты выбирают по репутации врача и отзывам.

---

ДАННЫЕ ИНСТРУМЕНТОВ:

{tool_output}"""

print(f"  Prompt size: {len(INTERPRET_PROMPT)} chars")

ollama = OpenAI(api_key=LLM_KEY, base_url=LLM_URL, timeout=120.0)
t0 = time.time()

resp = ollama.chat.completions.create(
    model=LLM_MODEL,
    messages=[
        {"role": "system", "content": "Ты — старший аналитик агентства AIM. Твоя задача — строить структурированные конкурентные анализы."},
        {"role": "user", "content": INTERPRET_PROMPT},
    ],
    temperature=0.3,
    max_tokens=4000,
)

interpretation = resp.choices[0].message.content or ""
usage = resp.usage.model_dump() if resp.usage else {}
print(f"  Interpretation done in {time.time()-t0:.0f}s. Tokens: {usage.get('total_tokens', '?')}")

# Сохраняем интерпретацию
path_int = os.path.join(RAW, "phase-1-interpretation.json")
with open(path_int, "w") as f:
    json.dump({
        "phase": "COMPETITORS",
        "type": "interpretation",
        "timestamp": datetime.now().isoformat(),
        "usage": usage,
        "interpretation": interpretation,
    }, f, ensure_ascii=False, indent=2)
print(f"  Saved: {path_int}")

# Сохраняем полный сводный файл фазы
path_full = os.path.join(RAW, "phase-1-full.json")
with open(path_full, "w") as f:
    json.dump({
        "phase": "COMPETITORS",
        "timestamp": datetime.now().isoformat(),
        "find_competitors": data,
        "ci_analysis": ci_data,
        "interpretation": interpretation,
    }, f, ensure_ascii=False, indent=2)
print(f"  Full dump: {path_full}")

# ══════════════════════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("PHASE 1 INTERPRETATION RESULT")
print("="*80)
print(interpretation)
print("\n---")
print(f"competitor_details count: {len(competitor_details)}")
for cd in competitor_details:
    print(f"  {cd.get('name')}: revenue={cd.get('revenue')}, trend={cd.get('revenue_trend')}, "
          f"doctors={cd.get('doctors_count')}, instagram={cd.get('instagram_username')} "
          f"({cd.get('instagram_subscribers')}), seo={cd.get('seo_score')}")
