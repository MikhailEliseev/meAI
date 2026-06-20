"""
E2E test for Phase 2 TECH AUDIT.
Runs run_pagespeed + run_tech_seo_audit, then LLM interpretation.
"""
import asyncio, json, sys, time, os

# Add hermes to path
sys.path.insert(0, "AIM/hermes/app")

TEST_URL = sys.argv[1] if len(sys.argv) > 1 else "https://docdeti.ru"

async def main():
    print(f"🧪 Phase 2 E2E test for: {TEST_URL}\n")

    # 1. Run tools
    print("=" * 60)
    print("STEP 1: run_pagespeed")
    print("=" * 60)
    t0 = time.monotonic()
    from app.tools.run_pagespeed import handle_run_pagespeed
    ps_result = await handle_run_pagespeed(url=TEST_URL)
    ps_data = json.loads(ps_result)
    t1 = time.monotonic()
    if "error" in ps_data:
        print(f"❌ PageSpeed FAILED ({t1-t0:.1f}s): {ps_data['error']}")
    else:
        mob = ps_data.get("mobile", {})
        desk = ps_data.get("desktop", {})
        print(f"✅ PageSpeed OK ({t1-t0:.1f}s)")
        print(f"   Mobile: score={mob.get('performance_score')}, LCP={mob.get('lcp')}, TBT={mob.get('tbt')}, CLS={mob.get('cls')}")
        print(f"   Desktop: score={desk.get('performance_score')}, LCP={desk.get('lcp')}, TBT={desk.get('tbt')}, CLS={desk.get('cls')}")

    print("\n" + "=" * 60)
    print("STEP 2: run_tech_seo_audit")
    print("=" * 60)
    from app.tools.run_tech_seo_audit import handle_run_tech_seo_audit
    seo_result = await handle_run_tech_seo_audit(url=TEST_URL)
    seo_data = json.loads(seo_result)
    t2 = time.monotonic()
    if "error" in seo_data:
        print(f"❌ Tech SEO FAILED ({t2-t1:.1f}s): {seo_data['error']}")
    else:
        s = seo_data.get("summary", {})
        t = seo_data.get("technical", {})
        print(f"✅ Tech SEO OK ({t2-t1:.1f}s)")
        print(f"   Pages scanned: {seo_data.get('pages_scanned')}")
        print(f"   Title: {s.get('title', 'N/A')[:80]}...")
        print(f"   Title OK: {s.get('title_ok')}, Desc OK: {s.get('description_ok')}")
        print(f"   H1: {s.get('h1_count')} (OK: {s.get('h1_ok')})")
        print(f"   Images: {s.get('images_total')} total, {s.get('images_alt_pct')}% with alt")
        print(f"   Structured data: {s.get('has_structured_data')}")
        ai = s.get("ai_optimization", {})
        print(f"   SSL: {t.get('ssl')}, robots.txt: {t.get('robots_txt')}, sitemap: {t.get('sitemap_xml')}")
        print(f"   AI: llms.txt={ai.get('has_llms_txt')}, ai.txt={ai.get('has_ai_txt')}, schema_types={ai.get('structured_data_types')}")

    # 2. Build compact data for LLM
    pagespeed_text = json.dumps({
        "mobile": ps_data.get("mobile", {}),
        "desktop": ps_data.get("desktop", {}),
    }, ensure_ascii=False, indent=2)

    pages = seo_data.get("pages", [])
    homepage = pages[0] if pages else {}
    seo_text = json.dumps({
        "url": seo_data.get("url"),
        "pages_scanned": seo_data.get("pages_scanned"),
        "technical": seo_data.get("technical"),
        "summary": seo_data.get("summary"),
        "homepage_meta": homepage.get("meta"),
        "homepage_headings": homepage.get("headings"),
        "homepage_images": homepage.get("images"),
        "homepage_links": homepage.get("links"),
        "homepage_structured_data": homepage.get("structured_data"),
    }, ensure_ascii=False, indent=2)

    data_text = f"## run_pagespeed\n{pagespeed_text}\n\n## run_tech_seo_audit\n{seo_text}"

    prompt = f"""Ты — технический SEO-аналитик. Проанализируй данные аудита сайта {TEST_URL}.

Данные:
{data_text}

Напиши краткий технический отчёт:
1. Скорость загрузки (mobile vs desktop) — ключевые метрики
2. SEO-диагностика — что хорошо, что плохо
3. Оптимизация для AI (llms.txt, ai.txt, Schema.org) — готов ли сайт к нейропоиску
4. Топ-3 критических проблемы
5. Что исправить в первую очередь

Формат: Markdown, без воды, конкретно."""

    print("\n" + "=" * 60)
    print("STEP 3: LLM Interpretation")
    print(f"Prompt size: {len(prompt)} chars")
    print("=" * 60)

    # Use OmniRoute
    from app.pipeline.engine import OMNIROUTE_URL, OMNIROUTE_AUTH, DEFAULT_MODEL

    model = os.environ.get("TEST_MODEL", DEFAULT_MODEL)
    print(f"Model: {model}")
    print(f"OmniRoute: {OMNIROUTE_URL}")

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
                    {"role": "system", "content": "Ты — технический SEO-аналитик. Отвечай на русском."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
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
    print(f"\n⏱️  Total E2E: {total:.1f}s (tools: {t2-t0:.1f}s, llm: {t4-t3:.1f}s)")
    print("✅ Phase 2 E2E test complete!")

if __name__ == "__main__":
    asyncio.run(main())
