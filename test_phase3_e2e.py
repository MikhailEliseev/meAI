"""
E2E test for Phase 3 SOCIAL VERIFIER.
Runs run_review_platforms (Perplexity), then LLM interpretation.
"""
import asyncio, json, sys, time, os

sys.path.insert(0, "AIM/hermes/app")

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://docdeti.ru"
TEST_NAME = sys.argv[2] if len(sys.argv) > 2 else "DocDeti"
TEST_CITY = sys.argv[3] if len(sys.argv) > 3 else "Москва"

async def main():
    print(f"🧪 Phase 3 E2E test for: {TEST_NAME} ({TEST_CITY})\n")

    # 1. Run tool
    print("=" * 60)
    print("STEP 1: run_review_platforms (Perplexity)")
    print("=" * 60)
    t0 = time.monotonic()
    from app.tools.run_review_platforms import handle_run_review_platforms
    result = await handle_run_review_platforms(url=TEST_URL, company_name=TEST_NAME, city=TEST_CITY)
    data = json.loads(result)
    t1 = time.monotonic()

    if "error" in data:
        print(f"❌ FAILED ({t1-t0:.1f}s): {data['error']}")
        return

    print(f"✅ OK ({t1-t0:.1f}s)")
    print(f"   Source: {data.get('source')}")
    print(f"   Platforms searched: {data.get('platforms_searched')}")
    print(f"   Platforms found: {data.get('platforms_found')}")
    print(f"   Total reviews est: {data.get('total_reviews_estimated')}")
    analysis_text = data.get("analysis", "")
    print(f"   Analysis length: {len(analysis_text)} chars")
    print(f"\n{'─' * 60}")
    print("RAW ANALYSIS (first 800 chars):")
    print("─" * 60)
    print(analysis_text[:800])
    if len(analysis_text) > 800:
        print(f"... (+{len(analysis_text) - 800} chars)")

    # 2. LLM Interpretation
    print("\n" + "=" * 60)
    print("STEP 2: LLM Interpretation")
    print("=" * 60)

    prompt = f"""Ты — аналитик репутации медицинских клиник. Проанализируй отзывы о клинике.

ГОРОД: {TEST_CITY}. СПЕЦИАЛИЗАЦИЯ КЛИНИКИ: детская клиника.

Данные об отзывах:
{analysis_text}

Напиши краткий анализ репутации:
1. Текущее состояние — рейтинги по платформам, общее количество отзывов
2. Что хвалят — главные сильные стороны в глазах пациентов (с примерами)
3. На что жалуются — системные проблемы и репутационные риски
4. Рекомендация — как улучшить репутацию (1-2 конкретных действия)

Формат: Markdown, без воды, конкретно."""

    print(f"Prompt size: {len(prompt)} chars")

    from app.pipeline.engine import OMNIROUTE_URL, OMNIROUTE_AUTH, DEFAULT_MODEL
    model = os.environ.get("TEST_MODEL", DEFAULT_MODEL)
    print(f"Model: {model}")

    import httpx
    t3 = time.monotonic()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{OMNIROUTE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OMNIROUTE_AUTH}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Ты — аналитик репутации медицинских клиник. Отвечай на русском."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
        )
        resp.raise_for_status()
        llm_result = resp.json()

    t4 = time.monotonic()
    content = llm_result["choices"][0]["message"]["content"]
    usage = llm_result.get("usage", {})

    print(f"\n✅ LLM done ({t4-t3:.1f}s)")
    print(f"   Tokens: in={usage.get('prompt_tokens')} out={usage.get('completion_tokens')}")
    print(f"\n{'─' * 60}")
    print("INTERPRETATION:")
    print("─" * 60)
    print(content)
    print("─" * 60)

    total = t4 - t0
    print(f"\n⏱️  Total E2E: {total:.1f}s (tool: {t1-t0:.1f}s, llm: {t4-t3:.1f}s)")
    print("✅ Phase 3 E2E test complete!")

if __name__ == "__main__":
    asyncio.run(main())
