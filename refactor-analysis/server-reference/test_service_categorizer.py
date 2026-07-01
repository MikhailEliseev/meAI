"""Tests for ServiceCategorizer — автоматическая категоризация услуг на основе prescan.

RED phase: tests will fail until ServiceCategorizer is implemented.
"""

from .service_categorizer import ServiceCategorizer, ServiceItem


def test_seo_poor_no_ads_no_social():
    """Test 1: плохой SEO, нет рекламы, нет соцсетей → recommended/base/next_stage."""
    cat = ServiceCategorizer()
    data = {
        'seo_score': 34,
        'has_sitemap': False,
        'has_structured_data': False,
        'total_pages': 25,
        'has_ads': False,
        'social_links': {},
    }
    result = cat.categorize(data)

    assert any(s.id == 'seo_rebuild' and s.category == 'recommended' for s in result), \
        'SEO < 40 should be recommended'
    assert any(s.id == 'yandex_direct' and s.category == 'recommended' for s in result), \
        'No ads should be recommended'
    assert any(s.id == 'social_media' and s.category == 'next_stage' for s in result), \
        'No social should be next_stage'
    assert any(s.id == 'audit' and s.category == 'base' and s.locked for s in result), \
        'Audit should be base + locked'
    assert len(result) == 5, f'Should have 5 services, got {len(result)}'
    print('Test 1 PASSED: плохой SEO + нет рекламы + нет соцсетей')


def test_seo_good_has_ads_active_social():
    """Test 2: хороший SEO, есть реклама, активные соцсети → optional."""
    cat = ServiceCategorizer()
    data = {
        'seo_score': 78,
        'has_sitemap': True,
        'has_structured_data': True,
        'total_pages': 45,
        'has_ads': True,
        'social_links': {'vk': 'active', 'telegram': 'active'},
    }
    result = cat.categorize(data)

    assert any(s.id == 'seo_rebuild' and s.category == 'optional' for s in result), \
        'Good SEO should be optional'
    assert any(s.id == 'yandex_direct' and s.category == 'optional' for s in result), \
        'Has ads should be optional'
    assert any(s.id == 'social_media' and s.category == 'optional' for s in result), \
        'Active social should be optional'
    print('Test 2 PASSED: хороший SEO + есть реклама + активные соцсети')


def test_critical_case_revenue_gap():
    """Test 3: критический случай — всё плохо + разрыв с конкурентами."""
    cat = ServiceCategorizer()
    data = {
        'seo_score': 25,
        'has_sitemap': False,
        'has_structured_data': False,
        'total_pages': 5,
        'has_ads': False,
        'social_links': {},
        'revenue_year': 5_000_000,
        'competitor_avg_revenue': 10_000_000,
    }
    result = cat.categorize(data)

    assert any(s.id == 'seo_rebuild' and s.category == 'recommended' for s in result), \
        'SEO 25 should be recommended'
    assert any(s.id == 'yandex_direct' and s.category == 'recommended' for s in result), \
        'No ads should be recommended'
    assert any(s.id == 'social_media' and s.category == 'next_stage' for s in result), \
        'No social should be next_stage'

    # Recommended services should be selected (revenue gap amplifies)
    seo = next(s for s in result if s.id == 'seo_rebuild')
    assert seo.selected is True, 'Recommended should be selected when revenue gap'
    print('Test 3 PASSED: критический случай + revenue gap')


def test_all_categories_valid():
    """Test 4: все категории валидны."""
    cat = ServiceCategorizer()
    data1 = {'seo_score': 34, 'has_sitemap': False, 'has_structured_data': False,
             'total_pages': 25, 'has_ads': False, 'social_links': {}}
    data2 = {'seo_score': 78, 'has_sitemap': True, 'has_structured_data': True,
             'total_pages': 45, 'has_ads': True,
             'social_links': {'vk': 'active', 'telegram': 'active'}}
    data3 = {'seo_score': 25, 'has_sitemap': False, 'has_structured_data': False,
             'total_pages': 5, 'has_ads': False, 'social_links': {},
             'revenue_year': 5_000_000, 'competitor_avg_revenue': 10_000_000}

    result1 = cat.categorize(data1)
    result2 = cat.categorize(data2)
    result3 = cat.categorize(data3)

    valid_categories = {'base', 'recommended', 'optional', 'next_stage'}
    for s in result1 + result2 + result3:
        assert s.category in valid_categories, f'Invalid category: {s.category}'
    print('Test 4 PASSED: all categories valid')


def test_audit_always_base_locked():
    """Test 5: аудит всегда base + locked."""
    cat = ServiceCategorizer()
    data1 = {'seo_score': 34, 'has_sitemap': False, 'has_structured_data': False,
             'total_pages': 25, 'has_ads': False, 'social_links': {}}
    data2 = {'seo_score': 78, 'has_sitemap': True, 'has_structured_data': True,
             'total_pages': 45, 'has_ads': True,
             'social_links': {'vk': 'active', 'telegram': 'active'}}
    data3 = {'seo_score': 25, 'has_sitemap': False, 'has_structured_data': False,
             'total_pages': 5, 'has_ads': False, 'social_links': {},
             'revenue_year': 5_000_000, 'competitor_avg_revenue': 10_000_000}

    for data in [data1, data2, data3]:
        result = cat.categorize(data)
        audit = next(s for s in result if s.id == 'audit')
        assert audit.category == 'base' and audit.locked is True, \
            'Audit must be base + locked'
    print('Test 5 PASSED: audit always base + locked')


if __name__ == '__main__':
    test_seo_poor_no_ads_no_social()
    test_seo_good_has_ads_active_social()
    test_critical_case_revenue_gap()
    test_all_categories_valid()
    test_audit_always_base_locked()
    print('\nALL TESTS PASSED')
