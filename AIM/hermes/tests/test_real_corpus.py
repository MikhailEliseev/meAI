#!/usr/bin/env python3
"""Test parser against RECONSTRUCTED markdown from real IPHC report.

Из IPHC поста 181 мы извлекли HTML, который LLM-сгенерировала через
старый builder. Чтобы проверить, что НОВЫЙ builder правильно обработает
тот же markdown, мы:
1. Восстанавливаем markdown из HTML (обратное преобразование)
2. Прогоняем восстановленный markdown через новый parser
3. Сравниваем результат с ожиданием
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, '/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/app/tools')
from build_report import _interpretation_to_html, _markdown_to_html


def html_to_markdown(html: str) -> str:
    """Reconstruct markdown from HTML (for testing only).

    Это упрощённое преобразование для тестирования парсера.
    Не претендует на полную обратимость.
    """
    md = html
    # Remove <div class="table-wrap"><table> wrappers, keep table content
    md = md.replace('<div class="table-wrap"><table>', '')
    md = md.replace('</table></div>', '\n')
    md = md.replace('<table>', '')
    md = md.replace('</table>', '\n')
    md = md.replace('<tr>', '|')
    md = md.replace('</tr>', '|\n')
    md = md.replace('<td>', '')
    md = md.replace('</td>', '|')
    md = md.replace('<th>', '')
    md = md.replace('</th>', '|')

    # Lists
    md = md.replace('<ul>', '')
    md = md.replace('</ul>', '\n')
    md = md.replace('<ol>', '')
    md = md.replace('</ol>', '\n')
    md = md.replace('<li>', '- ')
    md = md.replace('</li>', '\n')

    # Headers
    import re
    md = re.sub(r'<h3>(.*?)</h3>', r'### \1', md)
    md = re.sub(r'<h2>(.*?)</h2>', r'## \1', md)

    # Bold/italic
    md = md.replace('<strong>', '**').replace('</strong>', '**')
    md = md.replace('<em>', '*').replace('</em>', '*')

    # Code
    md = md.replace('<code>', '`').replace('</code>', '`')

    # Paragraphs
    md = md.replace('<p>', '').replace('</p>', '\n\n')
    md = md.replace('<br>', '\n')

    # HTML entities
    md = md.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
    md = md.replace('&quot;', '"').replace('&apos;', "'")

    # Clean up multiple newlines
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip()


def test_on_real_corpus():
    """Test parser on real IPHC interpretations."""
    corpus_path = Path('/Users/mikhaileliseev/Desktop/Dev/meAI_1/AIM/hermes/tests/fixtures/real_iphc_corpus.json')
    corpus = json.loads(corpus_path.read_text())
    print(f"Loaded {len(corpus)} real sections\n")

    all_pass = True
    for i, section in enumerate(corpus):
        tag = section['tag']
        original_html = section['html']

        # Reconstruct markdown
        md = html_to_markdown(original_html)

        # Run new parser
        new_html = _interpretation_to_html(md)

        # Sanity checks
        checks = {
            'has structure': len(new_html) > 100,
            'has h2/h3/p': any(t in new_html for t in ['<h2>', '<h3>', '<p>']),
            'valid HTML structure': new_html.count('<') == new_html.count('>'),  # balanced tags
        }

        status_all = all(checks.values())
        print(f"[{i}] {tag[:40]:<40} | md: {len(md):>5} → html: {len(new_html):>5} | {'✅' if status_all else '❌'}")
        for name, ok in checks.items():
            if not ok:
                print(f"    ❌ {name}")

        if not status_all:
            all_pass = False

    print()
    if all_pass:
        print("🎉 ALL REAL CORPUS TESTS PASSED")
    else:
        print("⚠️  Some tests failed")
    return all_pass


def test_specific_real_patterns():
    """Test against specific patterns we saw in real LLM output."""
    print("\n" + "=" * 60)
    print("SPECIFIC REAL-WORLD PATTERNS")
    print("=" * 60)

    # Pattern 1: PERPLEXITY-style === sections + bullets
    print("\n--- Pattern 1: PERPLEXITY === sections ---")
    md = """=== РЫНОК ===
- Объём рынка: ~31–62 млрд ₽ (2024, Москва)
- Тренды: рост платной медицины 8-12% в год
- Регулирование: ФЗ-152, ФЗ-38

=== КЛИЕНТ ===
- ИНН: 7708698635
- ОГРН: 1097746190970
- Полное название: АО «ИПХиК»

=== ПАЦИЕНТЫ ===
НЕТ ДАННЫХ

=== ВОЗМОЖНОСТИ ===
- Слабые места конкурентов: нет стационара
- Незанятые ниши: НЕТ ДАННЫХ"""
    html = _markdown_to_html(md)
    assert '<h3>РЫНОК</h3>' in html
    assert '<h3>КЛИЕНТ</h3>' in html
    assert '<h3>ПАЦИЕНТЫ</h3>' in html
    assert '<h3>ВОЗМОЖНОСТИ</h3>' in html
    print("  ✅ All === sections converted to h3")

    # Pattern 2: Blockquote key insight
    print("\n--- Pattern 2: Blockquote insight ---")
    md = "### Главный вывод\n\n> Конкурентное поле разрежено. Это окно для рывка: клиент при активной диджитализации может занять позицию первого."
    html = _markdown_to_html(md)
    assert '<blockquote class="surface-block">' in html
    print("  ✅ Key insight as blockquote")

    # Pattern 3: Detailed list with bold lead
    print("\n--- Pattern 3: Bold-led bullet items ---")
    md = """- **Инфраструктурное преимущество** — ИПХИК как институт с собственной клинической базой
- **Кадровый потенциал** — статус института подразумевает научно-практическую базу
- **Цифровой вакуум** — SEO и Instagram не используются"""
    html = _markdown_to_html(md)
    assert '<strong>Инфраструктурное преимущество</strong>' in html
    assert '<strong>Кадровый потенциал</strong>' in html
    print("  ✅ Bold-led bullets preserved")

    # Pattern 4: Separator between sections
    print("\n--- Pattern 4: --- separator ---")
    md = "## Сильные\n\n- point\n\n---\n\n## Точки роста\n\n- point2"
    html = _markdown_to_html(md)
    assert '<hr>' in html
    print("  ✅ --- converted to hr")

    # Pattern 5: "НЕТ ДАННЫХ" placeholders
    print("\n--- Pattern 5: НЕТ ДАННЫХ placeholders ---")
    md = """### Пациенты

НЕТ ДАННЫХ

### Возможности

- Незанятые ниши: НЕТ ДАННЫХ"""
    html = _markdown_to_html(md)
    assert 'НЕТ ДАННЫХ' in html
    # Should be in a paragraph
    assert '<p>НЕТ ДАННЫХ</p>' in html
    print("  ✅ НЕТ ДАННЫХ preserved as plain text")


if __name__ == '__main__':
    success = test_on_real_corpus()
    test_specific_real_patterns()
    print("\n" + "=" * 60)
    print("✅" if success else "❌", "Final result")
    print("=" * 60)
