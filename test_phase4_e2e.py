"""
E2E test for Phase 4 CONTENT ANALYSIS.
Runs run_content_analysis (Perplexity), then LLM interpretation.
"""
import asyncio, json, sys, time, os

sys.path.insert(0, "AIM/hermes/app")

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://iphk.ru"
TEST_NAME = sys.argv[2] if len(sys.argv) > 2 else "Институт пластической хирургии"
TEST_CITY = sys.argv[3] if len(sys.argv) > 3 else "Москва"

async def main():
    print(f"🧪 Phase 4 E2E test for: {TEST_NAME} ({TEST_CITY})\n")

    # 1. Run tool
    print("=" * 60)
    print("STEP 1: run_content_analysis (Perplexity)")
    print("=" * 60)
    t0 = time.monotonic()
    from app.tools.run_content_analysis import handle_run_content_analysis
    result = await handle_run_content_analysis(
        url=TEST_URL, company_name=TEST_NAME, city=TEST_CITY
    )
    data = json.loads(result)
    t1 = time.monotonic()

    if "error" in data:
        print(f"❌ FAILED ({t1-t0:.1f}s): {data['error']}")
        return

    analysis_text = data.get("analysis", "")
    source = data.get("source", "unknown")

    print(f"✅ OK ({t1-t0:.1f}s)")
    print(f"   Source: {source}")
    print(f"   Clinic: {data.get('clinic')}")
    print(f"   City: {data.get('city')}")
    print(f"   Analysis length: {len(analysis_text)} chars")

    # Validate
    if len(analysis_text) < 500:
        print(f"❌ FAILED: analysis too short ({len(analysis_text)} chars, expected >500)")
        return
    print(f"✅ Analysis length OK ({len(analysis_text)} chars)")

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

    prompt = f"""Твой анализ попадёт в секцию «Контент-анализ» финального отчёта для клиента.

Проанализируй контент сайта клиники.

## Формат ответа
1. **Текущее состояние** — какие типы страниц есть, общий объём, качество текстов
2. **Сильные страницы** — что работает хорошо (с конкретными примерами)
3. **Пробелы vs конкуренты** — каких страниц/тем нет, что есть у конкурентов
4. **Рекомендация** — что добавить в первую очередь (1-2 типа контента)

Сравнивай с конкурентами из competitors_context: у кого больше контента,
какие темы покрыты, какие форматы используют.
Если данные конкурентов недоступны — дай абсолютную оценку.

КОНТЕКСТ ОТ PERPLEXITY (анализ контента):
{analysis_text}

КОНТЕКСТ КОНКУРЕНТОВ (из Фазы 1):
Недоступен — дай абсолютную оценку контента."""

    print(f"Prompt size: {len(prompt)} chars")

    try:
        from app.pipeline.engine import OMNIROUTE_URL, OMNIROUTE_AUTH, DEFAULT_MODEL
    except ImportError:
        OMNIROUTE_URL = os.getenv("OMNIROUTE_URL", "http://omniroute:20128/v1")
        OMNIROUTE_AUTH = os.getenv("OMNIROUTE_AUTH", "")
        DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

    model = os.environ.get("TEST_MODEL", DEFAULT_MODEL)
    print(f"Model: {model}")

    import httpx
    t3 = time.monotonic()

    try:
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
                        {
                            "role": "system",
                            "content": "Ты — контент-аналитик маркетингового агентства AIM. Отвечай на русском.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1500,
                },
            )
            resp.raise_for_status()
            llm_result = resp.json()
    except Exception as e:
        print(f"⚠️ OmniRoute failed: {e}")
        print("Trying direct DeepSeek API...")
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not deepseek_key:
            print("❌ No DEEPSEEK_API_KEY — skipping LLM interpretation")
            print(f"\n⏱️  Total: {t1-t0:.1f}s (tool only, no LLM)")
            print("✅ Phase 4 E2E test complete (tool only)!")
            return

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {deepseek_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Ты — контент-аналитик маркетингового агентства AIM. Отвечай на русском.",
                        },
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
    print("✅ Phase 4 E2E test complete!")


if __name__ == "__main__":
    asyncio.run(main())
