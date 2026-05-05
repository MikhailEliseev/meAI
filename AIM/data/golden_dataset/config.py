"""
Golden Dataset Configuration

Эталонный датасет для валидации качества CI Deep Analyzer.

Содержит:
- 10-20 реальных медицинских сайтов (стоматология, косметология)
- Ожидаемые метрики для каждого сайта
- Benchmark для сравнения

Используется для:
- Регрессионного тестирования
- Проверки качества анализа
- Сравнения с конкурентами (Ahrefs, SEMrush)
"""

GOLDEN_DATASET = {
    "version": "1.0.0",
    "created_at": "2026-05-05",
    "total_sites": 15,
    "categories": {
        "dentistry": 10,
        "cosmetology": 5
    },
    "sites": [
        # Стоматология (10 сайтов)
        {
            "id": "dental_001",
            "name": "Tori Clinic",
            "url": "https://toriclinic.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "50-100",
                "quality_score": "70-85",
                "seo_coverage": "80-95%",
                "cwv_score": "60-80",
                "mobile_score": "75-90",
                "accessibility_score": "65-80",
                "security_score": "80-95"
            },
            "notes": "Крупная сеть клиник, хороший сайт"
        },
        {
            "id": "dental_002",
            "name": "Professional Clinic",
            "url": "https://profclinic.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "30-60",
                "quality_score": "65-80",
                "seo_coverage": "75-90%",
                "cwv_score": "55-75",
                "mobile_score": "70-85",
                "accessibility_score": "60-75",
                "security_score": "75-90"
            },
            "notes": "Средняя клиника, стандартный сайт"
        },
        {
            "id": "dental_003",
            "name": "CIDK",
            "url": "https://cidk.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "40-80",
                "quality_score": "70-85",
                "seo_coverage": "80-95%",
                "cwv_score": "60-80",
                "mobile_score": "75-90",
                "accessibility_score": "65-80",
                "security_score": "80-95"
            },
            "notes": "Известная клиника, качественный сайт"
        },
        {
            "id": "dental_004",
            "name": "Frau Clinic",
            "url": "https://frauklinik.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "30-60",
                "quality_score": "65-80",
                "seo_coverage": "75-90%",
                "cwv_score": "55-75",
                "mobile_score": "70-85",
                "accessibility_score": "60-75",
                "security_score": "75-90"
            },
            "notes": "Женская клиника, современный дизайн"
        },
        {
            "id": "dental_005",
            "name": "Клиника Юлии Щербатовой",
            "url": "https://juliasherbatova.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "20-40",
                "quality_score": "60-75",
                "seo_coverage": "70-85%",
                "cwv_score": "50-70",
                "mobile_score": "65-80",
                "accessibility_score": "55-70",
                "security_score": "70-85"
            },
            "notes": "Небольшая клиника, простой сайт"
        },
        {
            "id": "dental_006",
            "name": "Smile-at-Once",
            "url": "https://smile-at-once.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "100-200",
                "quality_score": "75-90",
                "seo_coverage": "85-95%",
                "cwv_score": "65-85",
                "mobile_score": "80-95",
                "accessibility_score": "70-85",
                "security_score": "85-95"
            },
            "notes": "Крупная сеть, очень хороший сайт"
        },
        {
            "id": "dental_007",
            "name": "Дентал Гуру",
            "url": "https://dentalguru.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "40-80",
                "quality_score": "70-85",
                "seo_coverage": "80-90%",
                "cwv_score": "60-80",
                "mobile_score": "75-90",
                "accessibility_score": "65-80",
                "security_score": "80-90"
            },
            "notes": "Средняя клиника, хороший SEO"
        },
        {
            "id": "dental_008",
            "name": "Немецкий Имплантологический Центр",
            "url": "https://www.german-implant-center.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "50-100",
                "quality_score": "75-90",
                "seo_coverage": "85-95%",
                "cwv_score": "65-85",
                "mobile_score": "80-95",
                "accessibility_score": "70-85",
                "security_score": "85-95"
            },
            "notes": "Премиум клиника, отличный сайт"
        },
        {
            "id": "dental_009",
            "name": "Зууб",
            "url": "https://zuub.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "30-60",
                "quality_score": "65-80",
                "seo_coverage": "75-90%",
                "cwv_score": "55-75",
                "mobile_score": "70-85",
                "accessibility_score": "60-75",
                "security_score": "75-90"
            },
            "notes": "Сеть клиник, стандартный сайт"
        },
        {
            "id": "dental_010",
            "name": "Дентал Фэнтези",
            "url": "https://dentalfantasy.ru/",
            "category": "dentistry",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "40-80",
                "quality_score": "70-85",
                "seo_coverage": "80-90%",
                "cwv_score": "60-80",
                "mobile_score": "75-90",
                "accessibility_score": "65-80",
                "security_score": "80-90"
            },
            "notes": "Детская стоматология, яркий дизайн"
        },

        # Косметология (5 сайтов)
        {
            "id": "cosm_001",
            "name": "Клиника Пирогова",
            "url": "https://pirogov-clinic.ru/",
            "category": "cosmetology",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "50-100",
                "quality_score": "75-90",
                "seo_coverage": "85-95%",
                "cwv_score": "65-85",
                "mobile_score": "80-95",
                "accessibility_score": "70-85",
                "security_score": "85-95"
            },
            "notes": "Известная клиника, отличный сайт"
        },
        {
            "id": "cosm_002",
            "name": "Клиника Семейная",
            "url": "https://semeynaya.ru/",
            "category": "cosmetology",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "100-200",
                "quality_score": "75-90",
                "seo_coverage": "85-95%",
                "cwv_score": "65-85",
                "mobile_score": "80-95",
                "accessibility_score": "70-85",
                "security_score": "85-95"
            },
            "notes": "Крупная сеть, очень хороший сайт"
        },
        {
            "id": "cosm_003",
            "name": "Клиника Медси",
            "url": "https://medsi.ru/",
            "category": "cosmetology",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "200-400",
                "quality_score": "80-95",
                "seo_coverage": "90-100%",
                "cwv_score": "70-90",
                "mobile_score": "85-95",
                "accessibility_score": "75-90",
                "security_score": "90-100"
            },
            "notes": "Крупнейшая сеть, топовый сайт"
        },
        {
            "id": "cosm_004",
            "name": "Клиника Чайка",
            "url": "https://chaikamed.ru/",
            "category": "cosmetology",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "100-200",
                "quality_score": "80-95",
                "seo_coverage": "85-95%",
                "cwv_score": "70-90",
                "mobile_score": "85-95",
                "accessibility_score": "75-90",
                "security_score": "90-100"
            },
            "notes": "Премиум клиника, топовый сайт"
        },
        {
            "id": "cosm_005",
            "name": "Клиника Реновацио",
            "url": "https://renovacio.ru/",
            "category": "cosmetology",
            "location": "Moscow",
            "expected_metrics": {
                "pages_analyzed": "40-80",
                "quality_score": "70-85",
                "seo_coverage": "80-90%",
                "cwv_score": "60-80",
                "mobile_score": "75-90",
                "accessibility_score": "65-80",
                "security_score": "80-90"
            },
            "notes": "Косметология, хороший сайт"
        }
    ],

    "benchmark_metrics": {
        "avg_pages_analyzed": 70,
        "avg_quality_score": 75,
        "avg_seo_coverage": 85,
        "avg_cwv_score": 70,
        "avg_mobile_score": 80,
        "avg_accessibility_score": 70,
        "avg_security_score": 85
    },

    "validation_rules": {
        "min_pages_analyzed": 10,
        "min_quality_score": 50,
        "min_seo_coverage": 60,
        "min_cwv_score": 40,
        "min_mobile_score": 50,
        "min_accessibility_score": 40,
        "min_security_score": 60
    }
}
