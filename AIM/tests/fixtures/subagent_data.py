"""Mock data fixtures for subagent tests

Realistic medical marketing domain data for testing.
"""

# Keyword Research Data
MEDICAL_KEYWORDS = [
    {
        "keyword": "dental implants cost",
        "volume": 12000,
        "difficulty": 65,
        "cpc": 8.50,
        "intent": "commercial",
        "compliance_risk": "low",
    },
    {
        "keyword": "buy oxycodone online",  # Risky keyword
        "volume": 5000,
        "difficulty": 45,
        "cpc": 12.00,
        "intent": "transactional",
        "compliance_risk": "high",  # Should be blocked
    },
    {
        "keyword": "teeth whitening near me",
        "volume": 8000,
        "difficulty": 55,
        "cpc": 6.20,
        "intent": "local",
        "compliance_risk": "low",
    },
    {
        "keyword": "cosmetic dentistry prices",
        "volume": 6500,
        "difficulty": 60,
        "cpc": 7.80,
        "intent": "commercial",
        "compliance_risk": "low",
    },
]

# SEMrush API Response Mock
SEMRUSH_RESPONSE = {
    "keywords": [
        {
            "keyword": "dental implants cost",
            "search_volume": 12000,
            "keyword_difficulty": 65,
            "cpc": 8.50,
            "intent": "commercial",
        },
        {
            "keyword": "dental implants near me",
            "search_volume": 10000,
            "keyword_difficulty": 60,
            "cpc": 7.20,
            "intent": "local",
        },
    ],
    "total_results": 2,
}

# Ahrefs API Response Mock
AHREFS_RESPONSE = {
    "keywords": [
        {
            "keyword": "dental implants cost",
            "volume": 12000,
            "difficulty": 65,
            "cpc": 8.50,
            "parent_topic": "dental implants",
        },
    ],
}

# Content Gap Data
COMPETITOR_CONTENT = [
    {
        "url": "https://competitor.com/dental-implants-guide",
        "title": "Complete Guide to Dental Implants",
        "word_count": 2500,
        "keywords": ["dental implants", "implant cost", "implant procedure"],
        "quality_score": 85,
        "headings": ["What are dental implants?", "Cost breakdown", "Procedure steps"],
    },
]

# Analytics Data
GA4_METRICS = {
    "sessions": 15000,
    "users": 12000,
    "bounce_rate": 0.45,
    "avg_session_duration": 180,
    "conversions": 150,
    "conversion_rate": 0.01,
    "top_pages": [
        {"path": "/dental-implants", "views": 5000},
        {"path": "/teeth-whitening", "views": 3000},
    ],
}

YANDEX_METRICS = {
    "visits": 14000,
    "visitors": 11000,
    "bounce_rate": 0.48,
    "avg_visit_duration": 175,
    "goals": 140,
    "conversion_rate": 0.01,
}

# Ads Campaign Data
YANDEX_CAMPAIGN = {
    "campaign_id": "12345",
    "name": "Dental Implants Campaign",
    "budget": 50000,
    "daily_budget": 1666,
    "status": "active",
    "ads": [
        {
            "ad_id": "67890",
            "title": "Dental Implants from $999",
            "text": "Professional dental implants. Free consultation.",
            "ctr": 0.05,
            "conversions": 25,
        },
    ],
}
