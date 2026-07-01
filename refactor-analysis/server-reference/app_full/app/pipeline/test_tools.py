"""Quick test of all 4 rewritten tools."""
import asyncio, json, sys, os

sys.path.insert(0, "/opt/hermes")

async def test():
    # Test 1: run_pagespeed
    print("=== Test 1: run_pagespeed ===")
    from app.tools.run_pagespeed import handle_run_pagespeed
    result = await handle_run_pagespeed(url="arclinic.ru")
    data = json.loads(result)
    if "error" in data:
        print(f"  FAIL: {data['error'][:100]}")
    else:
        mobile = data.get("mobile", {})
        desktop = data.get("desktop", {})
        print(f"  OK: mobile={mobile.get('performance_score','?')}/100, desktop={desktop.get('performance_score','?')}/100")

    # Test 2: run_review_platforms
    print("=== Test 2: run_review_platforms ===")
    from app.tools.run_review_platforms import handle_run_review_platforms
    result = await handle_run_review_platforms(url="arclinic.ru", company_name="Arclinic", city="Moscow")
    data = json.loads(result)
    if "error" in data:
        print(f"  WARN: {data['error'][:100]}")
    else:
        print(f"  OK: total={data.get('total_mentions','?')}, platforms={data.get('platforms_with_results','?')}")

    # Test 3: run_smi_mentions
    print("=== Test 3: run_smi_mentions ===")
    from app.tools.run_smi_mentions import handle_run_smi_mentions
    result = await handle_run_smi_mentions(url="arclinic.ru", company_name="Arclinic")
    data = json.loads(result)
    if "error" in data:
        print(f"  WARN: {data['error'][:100]}")
    else:
        print(f"  OK: total={data.get('total_mentions','?')}, cats={data.get('categories_with_mentions','?')}")

    # Test 4: run_content_gaps
    print("=== Test 4: run_content_gaps ===")
    from app.tools.run_content_gaps import handle_run_content_gaps
    result = await handle_run_content_gaps(url="arclinic.ru", client_site="arclinic.ru")
    data = json.loads(result)
    if "error" in data:
        print(f"  WARN: {data['error'][:100]}")
    else:
        print(f"  OK: topics={data.get('topics_analyzed','?')}, gaps={len(data.get('content_gaps',[]))}")

asyncio.run(test())
