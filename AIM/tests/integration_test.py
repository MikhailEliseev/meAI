"""
Integration Test for CI Deep Analyzer

Tests all 17 detectors on realistic HTML samples.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from aim.subagents.competitive_intel.agents.ci_deep_analyzer import CIDeepAnalyzer


# Sample HTML from medical clinic (realistic)
SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <title>Клиника пластической хирургии - Москва</title>
    <meta charset="UTF-8">
    <meta name="description" content="Пластическая хирургия в Москве">
    <link href="/bitrix/templates/main/style.css" rel="stylesheet">

    <!-- Analytics -->
    <script src="https://mc.yandex.ru/metrika/tag.js"></script>
    <script>ym(87654321, "init")</script>
    <script src="https://www.googletagmanager.com/gtm.js?id=GTM-ABC123"></script>

    <!-- Call Tracking -->
    <script src="https://calltouch.ru/widget.js"></script>

    <!-- Live Chat -->
    <script src="//code.jivosite.com/widget.js"></script>

    <!-- Retargeting -->
    <script src="https://connect.facebook.net/en_US/fbevents.js"></script>
    <script>fbq('init', '123456789')</script>

    <!-- CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
</head>
<body>
    <h1>Клиника пластической хирургии</h1>

    <!-- Messengers -->
    <a href="https://wa.me/79991234567">WhatsApp</a>
    <a href="https://t.me/clinic">Telegram</a>

    <!-- Booking -->
    <iframe src="https://n237778.yclients.com/"></iframe>

    <!-- Social Proof -->
    <div class="reviews">
        <h2>Отзывы наших клиентов</h2>
        <div class="rating">★★★★★ 4.9/5</div>
        <p>1000+ довольных клиентов</p>
    </div>

    <!-- Promo -->
    <div class="promo">
        <h3>Скидка 20% до конца месяца!</h3>
        <div class="countdown-timer">Осталось 5 дней</div>
    </div>

    <!-- CRM Form -->
    <form class="b24-web-form">
        <input type="text" name="name" placeholder="Ваше имя">
        <input type="tel" name="phone" placeholder="Телефон">
        <button type="submit">Записаться на консультацию</button>
    </form>
</body>
</html>
"""

SAMPLE_HEADERS = {
    'Server': 'nginx',
    'X-Powered-By': '1C-Bitrix',
    'Content-Type': 'text/html; charset=UTF-8'
}


async def test_detectors():
    """Test all detectors on sample HTML"""

    print("🧪 Integration Test: CI Deep Analyzer")
    print("=" * 60)

    # Create analyzer instance
    analyzer = CIDeepAnalyzer(
        agent_id="test_analyzer",
        database_url="sqlite:///test.db",
        vault_path="./test_vault"
    )

    print("\n📊 Testing 17 detectors on sample HTML...\n")

    # Test each detector
    results = {}

    # Sprint 1 detectors (10)
    print("Sprint 1 Detectors:")
    results['cms'] = analyzer._detect_cms(SAMPLE_HTML, SAMPLE_HEADERS)
    print(f"  ✅ CMS: {results['cms']['cms']} (confidence: {results['cms']['confidence']})")

    results['analytics'] = analyzer._detect_analytics(SAMPLE_HTML)
    detected_analytics = [k for k, v in results['analytics']['analytics'].items() if v['detected']]
    print(f"  ✅ Analytics: {len(detected_analytics)} tools detected")

    results['call_tracking'] = analyzer._detect_call_tracking(SAMPLE_HTML)
    print(f"  ✅ Call Tracking: {results['call_tracking']['provider'] if results['call_tracking']['detected'] else 'None'}")

    results['live_chat'] = analyzer._detect_live_chat(SAMPLE_HTML)
    print(f"  ✅ Live Chat: {results['live_chat']['provider'] if results['live_chat']['detected'] else 'None'}")

    results['messengers'] = analyzer._detect_messengers(SAMPLE_HTML)
    print(f"  ✅ Messengers: {results['messengers']['count']} detected")

    results['booking'] = analyzer._detect_booking_systems(SAMPLE_HTML)
    print(f"  ✅ Booking: {results['booking']['system'] if results['booking']['detected'] else 'None'}")

    results['payment'] = analyzer._detect_payment_systems(SAMPLE_HTML)
    print(f"  ✅ Payment: {results['payment']['count']} systems")

    results['cdn'] = analyzer._detect_cdn(SAMPLE_HTML)
    print(f"  ✅ CDN: {results['cdn']['provider'] if results['cdn']['detected'] else 'None'}")

    results['hosting'] = analyzer._detect_hosting(SAMPLE_HTML, SAMPLE_HEADERS)
    print(f"  ✅ Hosting: {results['hosting']['provider'] if results['hosting']['detected'] else 'Unknown'}")

    results['ab_testing'] = analyzer._detect_ab_testing(SAMPLE_HTML)
    print(f"  ✅ A/B Testing: {results['ab_testing']['tool'] if results['ab_testing']['detected'] else 'None'}")

    # Sprint 2 detectors (7)
    print("\nSprint 2 Detectors:")
    results['retargeting'] = analyzer._detect_retargeting(SAMPLE_HTML)
    print(f"  ✅ Retargeting: {results['retargeting']['count']} pixels")

    results['email_marketing'] = analyzer._detect_email_marketing(SAMPLE_HTML)
    print(f"  ✅ Email Marketing: {results['email_marketing']['platform'] if results['email_marketing']['detected'] else 'None'}")

    results['crm'] = analyzer._detect_crm(SAMPLE_HTML)
    print(f"  ✅ CRM: {results['crm']['crm'] if results['crm']['detected'] else 'None'}")

    results['quiz'] = analyzer._detect_quiz_lead_magnets(SAMPLE_HTML)
    print(f"  ✅ Quiz/Lead Magnets: {'Yes' if results['quiz']['detected'] else 'No'}")

    results['social_proof'] = analyzer._detect_social_proof(SAMPLE_HTML)
    print(f"  ✅ Social Proof: {results['social_proof']['count']} elements")

    results['geo'] = analyzer._detect_geo_targeting(SAMPLE_HTML)
    print(f"  ✅ Geo-Targeting: {'Yes' if results['geo']['detected'] else 'No'}")

    results['promo'] = analyzer._detect_promo_mechanics(SAMPLE_HTML)
    print(f"  ✅ Promo Mechanics: {results['promo']['count']} mechanics")

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  Total detectors tested: 17")

    detected_count = sum([
        1 if results['cms']['detected'] else 0,
        len(detected_analytics),
        1 if results['call_tracking']['detected'] else 0,
        1 if results['live_chat']['detected'] else 0,
        results['messengers']['count'],
        1 if results['booking']['detected'] else 0,
        results['payment']['count'],
        1 if results['cdn']['detected'] else 0,
        1 if results['hosting']['detected'] else 0,
        1 if results['ab_testing']['detected'] else 0,
        results['retargeting']['count'],
        1 if results['email_marketing']['detected'] else 0,
        1 if results['crm']['detected'] else 0,
        1 if results['quiz']['detected'] else 0,
        results['social_proof']['count'],
        1 if results['geo']['detected'] else 0,
        results['promo']['count']
    ])

    print(f"  Total detections: {detected_count}")
    print(f"  Expected: ~15-20 detections")

    if detected_count >= 10:
        print("\n✅ Integration Test PASSED!")
        return True
    else:
        print("\n❌ Integration Test FAILED - too few detections")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_detectors())
    sys.exit(0 if success else 1)
