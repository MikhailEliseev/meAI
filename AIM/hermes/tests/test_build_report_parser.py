#!/usr/bin/env python3
"""Test markdown + STATS parser на synthetic interpretation data."""
import sys
sys.path.insert(0, '/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/app/tools')

from build_report import (
    _interpretation_to_html,
    _markdown_to_html,
    _extract_stats_block,
    _inline_markdown,
    _markdown_table_to_html,
)


def test_inline_markdown():
    """Test bold/italic."""
    print("=== TEST 1: _inline_markdown ===")
    result = _inline_markdown("**bold text**")
    assert result == '<strong>bold text</strong>', f'Got: {result}'
    print(f'  ✅ **bold** → {result}')

    result = _inline_markdown("*italic text*")
    assert result == '<em>italic text</em>', f'Got: {result}'
    print(f'  ✅ *italic* → {result}')

    result = _inline_markdown("**bold** and *italic*")
    assert result == '<strong>bold</strong> and <em>italic</em>', f'Got: {result}'
    print(f'  ✅ mixed → {result}')


def test_stats_extraction():
    """Test STATS: block extraction."""
    print("\n=== TEST 2: _extract_stats_block ===")
    text = """### Текущее состояние

Выручка 4.1 млрд ₽, рост +24%.

STATS:
- value: "4,1 млрд ₽"
  label: "Выручка 2024"
- value: "+24%"
  label: "Рост за год"
- value: "1200"
  label: "Сотрудников"

### Заключение

Хорошо.
"""
    text_clean, stats_html = _extract_stats_block(text)
    print(f'  Stats HTML ({len(stats_html)} chars):')
    for line in stats_html.split('\n'):
        print(f'    {line}')
    assert 'glass-stats-wrap' in stats_html
    assert '4,1 млрд ₽' in stats_html
    assert '+24%' in stats_html
    assert 'STATS:' not in text_clean
    print(f'  ✅ STATS extracted, text cleaned')


def test_markdown_tables():
    """Test markdown table → HTML."""
    print("\n=== TEST 3: _markdown_table_to_html ===")
    table = """| Метрика | Значение |
|---------|----------|
| Выручка | 4.1 млрд |
| Рост | +24% |"""
    result = _markdown_table_to_html(table)
    print(f'  Result:')
    for line in result.split('<'):
        if line.strip():
            print(f'    <{line.strip()}')
    assert 'glass-table-wrap' in result
    assert '<thead>' in result
    assert '<th>Метрика</th>' in result
    assert '<td>4.1 млрд</td>' in result
    print(f'  ✅ Table converted correctly')


def test_full_markdown_to_html():
    """Test full markdown → HTML pipeline."""
    print("\n=== TEST 4: _markdown_to_html (full pipeline) ===")
    text = """## Текущее состояние

Выручка **4.1 млрд ₽**, рост *+24%* за год. Это **мощнейшая** клиника с историей с 2009 года.

## Что хорошо

- Стабильный рост выручки
- Сильный бренд в нише
- Квалифицированные врачи

## Что хромает

1. Слабый сайт
2. Нет Instagram
3. Мало отзывов

## Рекомендация

Улучшить цифровое присутствие.
"""
    html = _markdown_to_html(text)
    print(f'  HTML ({len(html)} chars):')
    for line in html.split('\n'):
        print(f'    {line}')
    assert '<h2>' in html
    assert '<strong>4.1 млрд ₽</strong>' in html
    assert '<em>+24%</em>' in html
    assert '<ul>' in html
    assert '<li>Стабильный рост выручки</li>' in html
    assert '<ol>' in html
    assert '<li>Слабый сайт</li>' in html
    assert '<p>' in html
    print(f'  ✅ Full pipeline works')


def test_stats_with_context():
    """Test STATS block extraction in context."""
    print("\n=== TEST 5: STATS in full interpretation ===")
    interp = """### Текущее состояние

Конкуренция на рынке эстетической медицины высокая.

STATS:
- value: "12"
  label: "Конкурентов в Москве"
- value: "₽340 млрд"
  label: "Объём рынка 2024"

### Главный вывод

Клиника в топ-3 по выручке.
"""
    html = _interpretation_to_html(interp)
    print(f'  HTML:')
    for line in html.split('\n'):
        print(f'    {line}')
    assert 'glass-stats-wrap' in html
    assert '12' in html
    assert '₽340 млрд' in html
    print(f'  ✅ STATS extracted in context')


def test_preserves_existing_html():
    """Test that existing HTML (LLM-written) is preserved."""
    print("\n=== TEST 6: Existing HTML preserved ===")
    existing = """<div class="glass-stats-wrap">
<div class="glass-stat">
<div class="glass-stat-value">1</div>
<div class="glass-stat-label">Конкурентов</div>
</div>
</div>"""
    html = _interpretation_to_html(existing)
    print(f'  Result: {html[:200]}...')
    # Should be preserved as-is
    assert 'glass-stats-wrap' in html
    assert 'glass-stat-value">1' in html
    print(f'  ✅ Existing HTML preserved')


def test_error_message():
    """Test error message handling."""
    print("\n=== TEST 7: Error message ===")
    err = "[Ошибка интерпретации: No module named 'run_agent']"
    html = _interpretation_to_html(err)
    print(f'  Result: {html}')
    assert 'text-dim' in html
    assert 'run_agent' in html  # not escaped away
    print(f'  ✅ Error rendered gracefully')


def test_empty():
    """Test empty input."""
    print("\n=== TEST 8: Empty input ===")
    assert _interpretation_to_html("") == ""
    assert _interpretation_to_html(None) == ""
    print(f'  ✅ Empty input handled')


if __name__ == '__main__':
    test_inline_markdown()
    test_stats_extraction()
    test_markdown_tables()
    test_full_markdown_to_html()
    test_stats_with_context()
    test_preserves_existing_html()
    test_error_message()
    test_empty()
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED")
    print("=" * 60)
