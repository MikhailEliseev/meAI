# tests/unit/test_wiki_synthesizer.py
import pytest
from meai.knowledge.wiki_synthesizer import WikiSynthesizer


@pytest.mark.asyncio
async def test_wiki_synthesizer_initialization():
    """Test WikiSynthesizer can be initialized"""
    synthesizer = WikiSynthesizer()
    assert synthesizer is not None


def test_extract_wikilinks():
    """Test extracting wikilinks from content"""
    synthesizer = WikiSynthesizer()

    content = """
    SEO best practices include [[keyword research]] and [[on-page optimization]].
    See also: [[content marketing]], [[link building]]
    """

    links = synthesizer.extract_wikilinks(content)

    assert "keyword research" in links
    assert "on-page optimization" in links
    assert "content marketing" in links
    assert "link building" in links
    assert len(links) == 4


@pytest.mark.asyncio
async def test_synthesize_knowledge():
    """Test synthesizing multiple knowledge items"""
    synthesizer = WikiSynthesizer()

    knowledge_items = [
        {
            "id": "k1",
            "content": "SEO requires [[keyword research]] and [[content optimization]].",
            "topic": "seo",
        },
        {
            "id": "k2",
            "content": "[[Keyword research]] helps identify search terms.",
            "topic": "seo",
        },
    ]

    synthesized = await synthesizer.synthesize(knowledge_items)

    assert "topic" in synthesized
    assert synthesized["topic"] == "seo"
    assert "wikilinks" in synthesized
    assert "keyword research" in synthesized["wikilinks"]
    assert "content optimization" in synthesized["wikilinks"]


def test_build_cross_references():
    """Test building cross-reference graph"""
    synthesizer = WikiSynthesizer()

    knowledge_items = [
        {
            "id": "k1",
            "content": "SEO includes [[keyword research]].",
            "topic": "seo",
        },
        {
            "id": "k2",
            "content": "[[Keyword research]] is important for [[SEO]].",
            "topic": "keyword-research",
        },
    ]

    graph = synthesizer.build_cross_references(knowledge_items)

    assert "keyword research" in graph
    assert "seo" in graph
    assert "k1" in graph["keyword research"]
    assert "k2" in graph["seo"]


def test_normalize_wikilink():
    """Test normalizing wikilink text"""
    synthesizer = WikiSynthesizer()

    assert synthesizer.normalize_wikilink("Keyword Research") == "keyword research"
    assert synthesizer.normalize_wikilink("  SEO Best Practices  ") == "seo best practices"
    assert synthesizer.normalize_wikilink("Content-Marketing") == "content-marketing"
