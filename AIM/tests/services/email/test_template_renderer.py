"""Tests for TemplateRenderer

Part of: Phase 11 Sprint 2 - Task 2.4
"""

import pytest
from pathlib import Path

from src.aim.services.email.template_renderer import TemplateRenderer


@pytest.fixture
def renderer():
    """Create TemplateRenderer instance."""
    return TemplateRenderer()


@pytest.mark.asyncio
async def test_render_hot_instant(renderer):
    """Test rendering hot_instant template."""
    context = {
        "name": "Иван Петров",
        "email": "ivan@example.com",
        "specialty": "стоматология",
        "service": "имплантация зубов",
    }

    html, text = await renderer.render(
        template_id="hot_instant",
        context=context,
        generate_ai_content=True,
    )

    # Check HTML content
    assert "Иван Петров" in html
    assert "стоматология" in html
    assert "имплантация зубов" in html
    assert "Михаил Елисеев" in html  # Default manager name
    assert "iamaim.ru" in html

    # Check text content
    assert "Иван Петров" in text
    assert "стоматология" in text
    assert "имплантация зубов" in text


@pytest.mark.asyncio
async def test_render_warm_day0(renderer):
    """Test rendering warm_day0 template."""
    context = {
        "name": "Мария Иванова",
        "specialty": "косметология",
    }

    html, text = await renderer.render(
        template_id="warm_day0",
        context=context,
        generate_ai_content=True,
    )

    assert "Мария Иванова" in html
    assert "косметология" in html
    assert "AIM Agency" in html


@pytest.mark.asyncio
async def test_render_warm_day3(renderer):
    """Test rendering warm_day3 template."""
    context = {
        "name": "Петр Сидоров",
        "specialty": "ортопедия",
    }

    html, text = await renderer.render(
        template_id="warm_day3",
        context=context,
        generate_ai_content=True,
    )

    assert "Петр Сидоров" in html
    assert "150%" in html  # Case study metric
    assert "кейс" in html.lower()


@pytest.mark.asyncio
async def test_render_warm_day7(renderer):
    """Test rendering warm_day7 template."""
    context = {
        "name": "Анна Смирнова",
        "specialty": "дерматология",
    }

    html, text = await renderer.render(
        template_id="warm_day7",
        context=context,
        generate_ai_content=True,
    )

    assert "Анна Смирнова" in html
    assert "дерматология" in html
    assert "99 000" in html  # Special offer price
    assert "Пакет" in html


@pytest.mark.asyncio
async def test_render_cold_weekly(renderer):
    """Test rendering cold_weekly template."""
    context = {
        "name": "Дмитрий Козлов",
        "specialty": "хирургия",
    }

    html, text = await renderer.render(
        template_id="cold_weekly",
        context=context,
        generate_ai_content=True,
    )

    assert "Дмитрий Козлов" in html
    assert "дайджест" in html.lower()
    assert "тренд" in html.lower()


@pytest.mark.asyncio
async def test_render_without_ai_content(renderer):
    """Test rendering without AI content generation."""
    context = {
        "name": "Тест",
        "specialty": "тест",
    }

    html, text = await renderer.render(
        template_id="hot_instant",
        context=context,
        generate_ai_content=False,
    )

    # Should still render template
    assert "Тест" in html
    assert len(html) > 0
    assert len(text) > 0


@pytest.mark.asyncio
async def test_render_with_defaults(renderer):
    """Test that default variables are added."""
    context = {"name": "Тест"}

    html, text = await renderer.render(
        template_id="hot_instant",
        context=context,
        generate_ai_content=False,
    )

    # Check default variables
    assert "Михаил Елисеев" in html
    assert "+7 (999) 123-45-67" in html
    assert "me@iamaim.ru" in html
    assert "iamaim.ru" in html


@pytest.mark.asyncio
async def test_render_subject_hot_instant(renderer):
    """Test rendering subject for hot_instant."""
    context = {"service": "имплантация зубов"}

    subject = renderer.render_subject(
        template_id="hot_instant", context=context
    )

    assert "имплантация зубов" in subject
    assert "запрос" in subject.lower()


@pytest.mark.asyncio
async def test_render_subject_warm_day0(renderer):
    """Test rendering subject for warm_day0."""
    context = {}

    subject = renderer.render_subject(
        template_id="warm_day0", context=context
    )

    assert "AIM Agency" in subject
    assert "добро пожаловать" in subject.lower()


@pytest.mark.asyncio
async def test_render_subject_warm_day3(renderer):
    """Test rendering subject for warm_day3."""
    context = {}

    subject = renderer.render_subject(
        template_id="warm_day3", context=context
    )

    assert "кейс" in subject.lower()
    assert "150%" in subject


@pytest.mark.asyncio
async def test_render_subject_warm_day7(renderer):
    """Test rendering subject for warm_day7."""
    context = {"specialty": "стоматология"}

    subject = renderer.render_subject(
        template_id="warm_day7", context=context
    )

    assert "стоматология" in subject
    assert "предложение" in subject.lower()


@pytest.mark.asyncio
async def test_render_subject_cold_weekly(renderer):
    """Test rendering subject for cold_weekly."""
    context = {}

    subject = renderer.render_subject(
        template_id="cold_weekly", context=context
    )

    assert "дайджест" in subject.lower()
    assert "📰" in subject


@pytest.mark.asyncio
async def test_ai_content_hot_intro(renderer):
    """Test AI content generation for hot leads."""
    context = {
        "specialty": "стоматология",
        "service": "имплантация зубов",
    }

    enriched = await renderer._enrich_with_ai("hot_instant", context)

    assert "ai_intro" in enriched
    assert "стоматология" in enriched["ai_intro"]
    assert "имплантация зубов" in enriched["ai_intro"]


@pytest.mark.asyncio
async def test_ai_content_warm_content(renderer):
    """Test AI content generation for warm leads."""
    context = {"specialty": "косметология"}

    enriched = await renderer._enrich_with_ai("warm_day0", context)

    assert "ai_content" in enriched
    assert "косметология" in enriched["ai_content"]


@pytest.mark.asyncio
async def test_ai_content_case_study(renderer):
    """Test AI content generation for case study."""
    context = {"specialty": "ортопедия"}

    enriched = await renderer._enrich_with_ai("warm_day3", context)

    assert "ai_case_study" in enriched
    assert "ортопедия" in enriched["ai_case_study"]


@pytest.mark.asyncio
async def test_ai_content_offer(renderer):
    """Test AI content generation for offer."""
    context = {"specialty": "дерматология"}

    enriched = await renderer._enrich_with_ai("warm_day7", context)

    assert "ai_offer" in enriched
    assert "дерматология" in enriched["ai_offer"]


@pytest.mark.asyncio
async def test_ai_content_digest(renderer):
    """Test AI content generation for digest."""
    context = {}

    enriched = await renderer._enrich_with_ai("cold_weekly", context)

    # Check digest content keys
    assert "ai_digest_intro" in enriched
    assert "trend_title" in enriched
    assert "weekly_tip" in enriched
    assert "case_title" in enriched
    assert "education_title" in enriched


@pytest.mark.asyncio
async def test_template_not_found(renderer):
    """Test rendering non-existent template."""
    context = {"name": "Тест"}

    with pytest.raises(Exception):  # Jinja2 TemplateNotFound
        await renderer.render(
            template_id="non_existent",
            context=context,
        )


@pytest.mark.asyncio
async def test_templates_directory_exists(renderer):
    """Test that templates directory exists."""
    assert renderer.templates_dir.exists()
    assert renderer.templates_dir.is_dir()


@pytest.mark.asyncio
async def test_all_templates_exist(renderer):
    """Test that all required templates exist."""
    required_templates = [
        "hot_instant",
        "warm_day0",
        "warm_day3",
        "warm_day7",
        "cold_weekly",
    ]

    for template_id in required_templates:
        html_path = renderer.templates_dir / f"{template_id}.html"
        txt_path = renderer.templates_dir / f"{template_id}.txt"

        assert html_path.exists(), f"Missing {template_id}.html"
        assert txt_path.exists(), f"Missing {template_id}.txt"


@pytest.mark.asyncio
async def test_html_escaping(renderer):
    """Test that HTML is properly escaped."""
    context = {
        "name": "<script>alert('xss')</script>",
        "specialty": "test",
    }

    html, text = await renderer.render(
        template_id="hot_instant",
        context=context,
        generate_ai_content=False,
    )

    # HTML should be escaped
    assert "<script>" not in html
    assert "&lt;script&gt;" in html or "alert" not in html
