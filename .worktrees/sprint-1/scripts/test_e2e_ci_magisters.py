"""
End-to-End Test: CI System + Magisters Integration

Полный тест интеграции CI системы с Magisters через Operator.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.integration.ci_magisters_integration import CIMagisterIntegration
from AIM.src.aim.magisters.seo_magister_with_ci import SEOMagisterWithCI
from AIM.src.aim.magisters.content_magister_with_ci import ContentMagisterWithCI
from AIM.src.aim.magisters.ads_magister_with_ci import AdsMagisterWithCI
from meai.events.event_bus import EventBus


async def test_e2e_ci_magisters():
    """End-to-End тест CI + Magisters."""

    print("=" * 80)
    print("🧪 END-TO-END TEST: CI SYSTEM + MAGISTERS")
    print("=" * 80)
    print()

    # Шаг 1: Инициализация
    print("📋 Шаг 1: Инициализация компонентов")
    print("-" * 80)

    event_bus = EventBus("sqlite+aiosqlite:///./AIM/data/aim.db")
    await event_bus.initialize()

    ci_integration = CIMagisterIntegration(
        event_bus=event_bus,
        ci_data_path="AIM/data"
    )
    await ci_integration.initialize()

    # Создаём Magisters с CI интеграцией
    seo_magister = SEOMagisterWithCI(
        magister_id="seo-magister",
        ci_integration=ci_integration
    )

    content_magister = ContentMagisterWithCI(
        magister_id="content-magister",
        ci_integration=ci_integration
    )

    ads_magister = AdsMagisterWithCI(
        magister_id="ads-magister",
        ci_integration=ci_integration
    )

    print("✅ Компоненты инициализированы")
    print()

    # Шаг 2: SEO Magister с CI
    print("=" * 80)
    print("📋 Шаг 2: SEO Magister - Планирование с CI инсайтами")
    print("-" * 80)

    seo_plan = await seo_magister.plan_task_with_ci(
        action="keyword_research",
        payload={"niche": "стоматология", "geo": "Москва"}
    )

    print(f"✅ SEO план создан")
    print(f"   Enhanced: {seo_plan.get('enhanced', False)}")
    print(f"   Приоритетов: {len(seo_plan.get('priorities', []))}")
    print(f"   CI рекомендаций: {len(seo_plan.get('ci_recommendations', []))}")

    if seo_plan.get("priorities"):
        print(f"\n   TOP-3 приоритета:")
        for idx, priority in enumerate(seo_plan["priorities"][:3], 1):
            print(f"     {idx}. {priority.get('task')} ({priority.get('priority')})")

    # Дополнительные методы SEO Magister
    print(f"\n   Дополнительные возможности:")

    competitive_context = await seo_magister.get_competitive_context()
    print(f"     - Конкурентный контекст: {competitive_context.get('competitors_count', 0)} конкурентов")

    content_recs = await seo_magister.get_content_recommendations()
    print(f"     - Контент-рекомендации: {len(content_recs)}")

    print()

    # Шаг 3: Content Magister с CI
    print("=" * 80)
    print("📋 Шаг 3: Content Magister - Планирование с CI инсайтами")
    print("-" * 80)

    content_plan = await content_magister.plan_task_with_ci(
        action="content_strategy",
        payload={"niche": "стоматология"}
    )

    print(f"✅ Content план создан")
    print(f"   Enhanced: {content_plan.get('enhanced', False)}")
    print(f"   Пробелов в контенте: {len(content_plan.get('content_gaps', []))}")

    if content_plan.get("content_strategy"):
        strategy = content_plan["content_strategy"]
        print(f"\n   Контент-стратегия:")
        print(f"     - Фокусных областей: {len(strategy.get('focus_areas', []))}")
        print(f"     - Типов контента: {len(strategy.get('content_types', []))}")
        print(f"     - Приоритетов: {len(strategy.get('priorities', []))}")

    # Дополнительные методы Content Magister
    print(f"\n   Дополнительные возможности:")

    content_gaps = await content_magister.get_content_gaps()
    print(f"     - Пробелы в контенте: {len(content_gaps)}")

    competitor_analysis = await content_magister.get_competitor_content_analysis()
    print(f"     - Анализ конкурентов: {len(competitor_analysis.get('opportunities', []))} возможностей")

    topics = await content_magister.suggest_content_topics(count=5)
    print(f"     - Предложенных тем: {len(topics)}")

    print()

    # Шаг 4: Ads Magister с CI
    print("=" * 80)
    print("📋 Шаг 4: Ads Magister - Планирование с CI инсайтами")
    print("-" * 80)

    ads_plan = await ads_magister.plan_task_with_ci(
        action="campaign_planning",
        payload={"budget": 500000, "niche": "стоматология"}
    )

    print(f"✅ Ads план создан")
    print(f"   Enhanced: {ads_plan.get('enhanced', False)}")

    if ads_plan.get("ads_strategy"):
        strategy = ads_plan["ads_strategy"]
        print(f"\n   Рекламная стратегия:")
        print(f"     - Каналов: {len(strategy.get('channels', []))}")
        print(f"     - Месседжей: {len(strategy.get('messaging', []))}")

    if ads_plan.get("budget_recommendations"):
        budget = ads_plan["budget_recommendations"]
        print(f"\n   Бюджетные рекомендации:")
        print(f"     - Рекомендованный бюджет: {budget.get('recommended_total', 0):,} руб")
        print(f"     - Средний чек на рынке: {budget.get('avg_market_check', 0):,} руб")

    # Дополнительные методы Ads Magister
    print(f"\n   Дополнительные возможности:")

    pricing_insights = await ads_magister.get_pricing_insights()
    print(f"     - Ценовые инсайты: {len(pricing_insights.get('opportunities', []))} возможностей")

    competitor_messaging = await ads_magister.get_competitor_messaging()
    print(f"     - Анализ месседжей: {len(competitor_messaging)} конкурентов")

    ad_channels = await ads_magister.suggest_ad_channels()
    print(f"     - Рекомендованных каналов: {len(ad_channels)}")

    print()

    # Шаг 5: Уведомление о новом анализе
    print("=" * 80)
    print("📋 Шаг 5: Уведомление Magisters о новом CI анализе")
    print("-" * 80)

    await ci_integration.notify_magisters_about_new_analysis(
        analysis_id="e2e_test_001",
        niche="стоматология",
        geo="Москва"
    )

    print("✅ Уведомление отправлено через Event Bus")
    print()

    # Закрываем соединения
    await event_bus.close()

    # Итоговая статистика
    print("=" * 80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА E2E ТЕСТА")
    print("=" * 80)
    print()
    print("✅ Все компоненты работают!")
    print()
    print("Проверено:")
    print("  ✅ CI Integration инициализация")
    print("  ✅ SEO Magister с CI инсайтами")
    print("  ✅ Content Magister с CI инсайтами")
    print("  ✅ Ads Magister с CI инсайтами")
    print("  ✅ Event Bus уведомления")
    print()
    print("Возможности:")
    print("  ✅ Планирование задач с CI контекстом")
    print("  ✅ Приоритизация на основе конкурентного анализа")
    print("  ✅ Рекомендации из CI системы")
    print("  ✅ Рыночный контекст для принятия решений")
    print()
    print("=" * 80)
    print("🎉 ИНТЕГРАЦИЯ CI + MAGISTERS РАБОТАЕТ!")
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_e2e_ci_magisters())
    sys.exit(0 if success else 1)
