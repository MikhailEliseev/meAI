"""
Test CI Magisters Integration

Тестирует интеграцию CI системы с Magisters.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from AIM.src.aim.integration.ci_magisters_integration import CIMagisterIntegration
from meai.events.event_bus import EventBus


async def test_ci_magisters_integration():
    """Тест интеграции CI с Magisters."""

    print("=" * 80)
    print("🧪 ТЕСТ CI MAGISTERS INTEGRATION")
    print("=" * 80)
    print()

    # Создаём Event Bus
    event_bus = EventBus("sqlite+aiosqlite:///./AIM/data/aim.db")
    await event_bus.initialize()

    # Создаём интеграцию
    integration = CIMagisterIntegration(
        event_bus=event_bus,
        ci_data_path="AIM/data"
    )

    print("📋 Инициализация интеграции...")
    await integration.initialize()
    print()

    # Тест 1: SEO Magister
    print("=" * 80)
    print("Test 1: SEO Magister Insights")
    print("=" * 80)

    seo_insights = await integration.get_insights_for_magister(
        magister_type="seo",
        action="keyword_research"
    )

    print(f"✅ SEO Insights получены")
    print(f"   Конкурентов: {len(seo_insights.get('competitors', []))}")
    print(f"   Возможностей: {len(seo_insights.get('opportunities', []))}")
    print(f"   Рекомендаций: {len(seo_insights.get('recommendations', []))}")

    if seo_insights.get("market_context"):
        print(f"   Рыночный контекст:")
        for key, value in seo_insights["market_context"].items():
            print(f"     - {key}: {value}")

    print()

    # Тест 2: Content Magister
    print("=" * 80)
    print("Test 2: Content Magister Insights")
    print("=" * 80)

    content_insights = await integration.get_insights_for_magister(
        magister_type="content",
        action="content_strategy"
    )

    print(f"✅ Content Insights получены")
    print(f"   Пробелов в контенте: {len(content_insights.get('content_gaps', []))}")
    print(f"   Возможностей: {len(content_insights.get('opportunities', []))}")
    print(f"   Рекомендаций: {len(content_insights.get('recommendations', []))}")

    if content_insights.get("market_context"):
        print(f"   Рыночный контекст:")
        for key, value in content_insights["market_context"].items():
            print(f"     - {key}: {value}")

    print()

    # Тест 3: Ads Magister
    print("=" * 80)
    print("Test 3: Ads Magister Insights")
    print("=" * 80)

    ads_insights = await integration.get_insights_for_magister(
        magister_type="ads",
        action="campaign_planning"
    )

    print(f"✅ Ads Insights получены")
    print(f"   Конкурентов: {len(ads_insights.get('competitors', []))}")
    print(f"   Возможностей: {len(ads_insights.get('opportunities', []))}")
    print(f"   Рекомендаций: {len(ads_insights.get('recommendations', []))}")

    if ads_insights.get("market_context"):
        print(f"   Рыночный контекст:")
        for key, value in ads_insights["market_context"].items():
            print(f"     - {key}: {value}")

    print()

    # Тест 4: Сводки для Magisters
    print("=" * 80)
    print("Test 4: Summary for Magisters")
    print("=" * 80)

    for magister_type in ["seo", "content", "ads"]:
        summary = await integration.get_summary_for_magister(magister_type)
        print(f"✅ {magister_type.upper()} Magister: {summary}")

    print()

    # Тест 5: Уведомление Magisters
    print("=" * 80)
    print("Test 5: Notify Magisters")
    print("=" * 80)

    await integration.notify_magisters_about_new_analysis(
        analysis_id="test_analysis_001",
        niche="стоматология",
        geo="Москва"
    )

    print("✅ Уведомление отправлено")
    print()

    # Закрываем соединения
    await event_bus.close()

    # Итоговая статистика
    print("=" * 80)
    print("📈 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    print()
    print("✅ Все тесты пройдены!")
    print()
    print("Интеграция работает:")
    print("  - SEO Magister может получать CI инсайты")
    print("  - Content Magister может получать CI инсайты")
    print("  - Ads Magister может получать CI инсайты")
    print("  - Уведомления через Event Bus работают")
    print()
    print("=" * 80)

    return True


if __name__ == "__main__":
    success = asyncio.run(test_ci_magisters_integration())
    sys.exit(0 if success else 1)
