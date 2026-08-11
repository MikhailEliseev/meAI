"""LLM-as-judge — качественная оценка ответа по рубрике (0-5).

Опционален (только с --refresh --judge). Использует тот же шлюз
OMNIROUTE/GLM, что и основной чат. Возвращает JSON-скор по 4 критериям.

Внимание: judge НЕ должен знать про диагноз — он просто оценивает ответ
как независимый эксперт. Это даёт несмещённый качественный скор.
"""
from __future__ import annotations

import json
import re


_JUDGE_PROMPT = """Ты — независимый эксперт-аудитор AI-ассистента для медицинского маркетинга.
Оцени ответ ассистента клинике. Ответ должен быть ПОЛЕЗНЫМ, РЕЛЕВАНТНЫМ, ОПИРаТЬСЯ на факты.

=== ДАННЫЕ, которые ассистент получил (таблицы/факты из источников) ===
{data}

=== ОТВЕТ АССИСТЕНТА (аналитический текст) ===
{answer}

Оцени по 4 критериям от 0 до 5 (можно дробно):
1. "grounding" — опирается ли ответ на приведённые данные? (5=все утверждения из данных, 0=выдумки)
2. "relevance" — насколько ответ полезен и по делу для клиники? (5=конкретно и ценно, 0=вода)
3. "actionability" — есть ли конкретные действия/рекомендации? (5=чёткие шаги, 0=общие слова)
4. "sales_value" — подталкивает ли к действию/покупке? (5=сильное КП, 0=нейтрально)

Верни СТРОГО JSON без markdown:
{{"grounding": 0.0, "relevance": 0.0, "actionability": 0.0, "sales_value": 0.0, "comment": "кратко"}}
"""


async def judge_snapshot(snapshot: dict) -> dict:
    """Оценивает ответ в snapshot. Возвращает {scores..., total, comment}."""
    try:
        from app.llm import get_client
        from app.config import LLM_MODEL, OMNIROUTE_URL, OMNIROUTE_AUTH
    except Exception as e:
        return {"error": f"config import: {e}", "total": 0}

    events = snapshot.get("events", {})
    data = "\n".join(events.get("formatted_blocks", [])) or "(данные не получены)"
    answer = events.get("llm_text", "") or "(ответ пуст)"
    # урезать, чтобы не разорвать контекст
    if len(data) > 6000:
        data = data[:6000] + "\n…(обрезано)"
    if len(answer) > 4000:
        answer = answer[:4000] + "\n…(обрезано)"

    prompt = _JUDGE_PROMPT.format(data=data, answer=answer)
    messages = [{"role": "user", "content": prompt}]

    # Q5: retry на пустой/некорректный ответ (GLM иногда отдаёт пустоту).
    last_raw = ""
    for attempt in range(3):
        try:
            client = get_client()
            resp = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=400,
            )
            raw = (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_raw = f"<exception: {e}>"
            continue
        if not raw:
            last_raw = "<empty>"
            continue
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            last_raw = raw[:200]
            continue
        try:
            scores = json.loads(m.group(0))
        except json.JSONDecodeError:
            last_raw = raw[:200]
            continue
        keys = ["grounding", "relevance", "actionability", "sales_value"]
        vals = [float(scores.get(k, 0)) for k in keys]
        scores["total"] = round(sum(vals) / len(vals), 2)
        return scores

    return {"error": f"judge gave no JSON after 3 attempts: {last_raw}", "total": 0}
