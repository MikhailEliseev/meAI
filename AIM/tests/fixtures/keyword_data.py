"""Mock keyword data fixtures for testing"""

# SEMrush mock data
SEMRUSH_MOCK_RESPONSE = {
    "data": [
        {
            "Ph": "dental implants",
            "Nq": 5000,
            "Cp": 12.50,
            "Co": 0.85,
            "Nr": 1500000,
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        },
        {
            "Ph": "dental implants cost",
            "Nq": 3000,
            "Cp": 15.00,
            "Co": 0.90,
            "Nr": 800000,
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        },
        {
            "Ph": "dental implants near me",
            "Nq": 8000,
            "Cp": 18.00,
            "Co": 0.95,
            "Nr": 500000,
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        },
        {
            "Ph": "what are dental implants",
            "Nq": 2000,
            "Cp": 5.00,
            "Co": 0.40,
            "Nr": 2000000,
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        },
        {
            "Ph": "best dental implants",
            "Nq": 1500,
            "Cp": 10.00,
            "Co": 0.75,
            "Nr": 1200000,
            "Td": "0,0,0,0,0,0,0,0,0,0,0,0",
        },
    ]
}

# Ahrefs mock data
AHREFS_MOCK_RESPONSE = {
    "keywords": [
        {
            "keyword": "dental implants",
            "volume": 5000,
            "keyword_difficulty": 75,
            "cpc": 12.50,
            "clicks": 3500,
            "parent_topic": "dental procedures",
        },
        {
            "keyword": "dental implants cost",
            "volume": 3000,
            "keyword_difficulty": 80,
            "cpc": 15.00,
            "clicks": 2100,
            "parent_topic": "dental procedures",
        },
        {
            "keyword": "dental implants near me",
            "volume": 8000,
            "keyword_difficulty": 85,
            "cpc": 18.00,
            "clicks": 5600,
            "parent_topic": "dental procedures",
        },
        {
            "keyword": "what are dental implants",
            "volume": 2000,
            "keyword_difficulty": 35,
            "cpc": 5.00,
            "clicks": 1400,
            "parent_topic": "dental education",
        },
        {
            "keyword": "best dental implants",
            "volume": 1500,
            "keyword_difficulty": 65,
            "cpc": 10.00,
            "clicks": 1050,
            "parent_topic": "dental procedures",
        },
    ]
}

# Zero volume response
ZERO_VOLUME_RESPONSE = {"data": []}

# Suggestions response
SUGGESTIONS_RESPONSE = {
    "data": [
        {"Ph": "dental implants procedure", "Nq": 1200},
        {"Ph": "dental implants recovery", "Nq": 900},
        {"Ph": "dental implants vs dentures", "Nq": 800},
        {"Ph": "dental implants pain", "Nq": 700},
        {"Ph": "dental implants types", "Nq": 600},
    ]
}
