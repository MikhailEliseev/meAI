#!/usr/bin/env python3
"""Phase 1 v2 — reuse saved find_competitors, test CI analysis with fixed data flow."""
import json, os, time
from datetime import datetime
from openai import OpenAI
import httpx
import asyncio

PROJECT = "/opt/data/projects/iphk.ru"
RAW = os.path.join(PROJECT, "raw-data")
LLM_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
LLM_KEY = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
if not LLM_KEY:
    raise RuntimeError("No LLM API key in env")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

# Load find_competitors from saved
with open(os.path.join(RAW, "phase-1-find-competitors-raw.json")) as f:
    fc_data = json.load(f)

competitors = fc_data["competitors"]
ci_competitors = []
for c in competitors:
    ci_competitors.append({
        "brand_name": c.get("brand_name") or c.get("legal_name", "?"),
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

print(f"Loaded {len(ci_competitors)} competitors")
for c in ci_competitors:
    print(f"  {c['brand_name']}: website={c['website'][:40]}, revenue={c['revenue_year']}, trend={c['revenue_trend']}")

async def run_ci():
    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(
            "http://aim-app:8000/api/competitors/analyze",
            json={
                "url": "https://iphk.ru",
                "specialization": "пластическая хирургия и косметология",
                "city": "Москва",
                "services": [],
                "competitors": ci_competitors,
                "tier": "quick",
            },
        )
        resp.raise_for_status()
        return resp.json()

print("\nRunning CI analysis...")
ci_data = asyncio.run(run_ci())

cds = ci_data.get("competitor_details", [])
print(f"\ncompetitor_details: {len(cds)} entries")
for d in cds:
    print(f"  {d.get('name')}: revenue={d.get('revenue')}, trend={d.get('revenue_trend')}, "
          f"doctors={d.get('doctors_count')}, instagram={d.get('instagram_username')}"
          f"({d.get('instagram_subscribers')}), seo={d.get('seo_score')}, rating={d.get('gm_rating')}")

# Save
with open(os.path.join(RAW, "phase-1-ci-analysis-v2.json"), "w") as f:
    json.dump(ci_data, f, ensure_ascii=False, indent=2)
print("\nSaved phase-1-ci-analysis-v2.json")

# ── LLM Interpretation ──
print("\n── LLM Interpretation ──")
chat_summary = ci_data.get("chat_summary", "")
feature_matrix = ci_data.get("feature_matrix", {})
top_rec = ci_data.get("top_recommendation", "")
tactics = ci_data.get("steal_worthy_tactics", [])

# Build tool output sections
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
parts.append("competitor_details:")
for cd in cds:
    rev = cd.get("revenue")
    rev_str = f"revenue={rev:,.0f}".replace(",", " ") if rev else "revenue=null"
    parts.append(
        f"- {cd.get('name', '?')}: {rev_str}, "
        f"revenue_trend={cd.get('revenue_trend') or 'null'}, "
        f"seo_score={cd.get('seo_score')}, "
        f"gm_rating={cd.get('gm_rating')}"
    )

parts.append(f"\nchat_summary: {chat_summary[:500] if chat_summary else 'Нет данных'}")

if feature_matrix:
    parts.append("\nfeature_matrix:")
    fm_list = feature_matrix.get("competitors", []) if isinstance(feature_matrix, dict) else []
    for fm in fm_list:
        parts.append(
            f"- {fm.get('name', '?')}: seo_score={fm.get('seo_score')}, online_booking={fm.get('online_booking')}"
        )

tactics_str = "; ".join([t.get("tactic", str(t)) for t in tactics[:5]]) if tactics else "нет"
parts.append(f"\nsteal_worthy_tactics: {len(tactics)} тактик — {tactics_str[:300]}")
parts.append(f"\ntop_recommendation: {top_rec[:300] if top_rec else 'Нет'}")

tool_output = "\n".join(parts)

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

ollama = OpenAI(api_key=LLM_KEY, base_url=LLM_URL, timeout=120.0)
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

path_int = os.path.join(RAW, "phase-1-interpretation-v2.json")
with open(path_int, "w") as f:
    json.dump({
        "phase": "COMPETITORS",
        "type": "interpretation",
        "timestamp": datetime.now().isoformat(),
        "usage": usage,
        "interpretation": interpretation,
    }, f, ensure_ascii=False, indent=2)

print("\n" + "="*80)
print("PHASE 1 INTERPRETATION RESULT (v2)")
print("="*80)
print(interpretation)
