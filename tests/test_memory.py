"""Test suite for meAI assistant."""

import pytest
from meai.memory.obsidian import ObsidianMemory
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_vault():
    """Create a temporary Obsidian vault for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_obsidian_memory_init(temp_vault):
    """Test ObsidianMemory initialization."""
    memory = ObsidianMemory(temp_vault)
    assert memory.vault_path.exists()


def test_write_and_read_note(temp_vault):
    """Test writing and reading notes."""
    memory = ObsidianMemory(temp_vault)

    content = "# Test Note\n\nThis is a test."
    memory.write_note("test.md", content)

    read_content = memory.read_note("test.md")
    assert read_content == content


def test_write_note_with_frontmatter(temp_vault):
    """Test writing notes with frontmatter."""
    memory = ObsidianMemory(temp_vault)

    content = "# Test Note"
    frontmatter = {"title": "Test", "type": "note"}
    memory.write_note("test.md", content, frontmatter=frontmatter)

    read_content = memory.read_note("test.md")
    assert "---" in read_content
    assert "title: Test" in read_content
    assert "type: note" in read_content


def test_append_to_note(temp_vault):
    """Test appending to existing notes."""
    memory = ObsidianMemory(temp_vault)

    memory.write_note("test.md", "First line")
    memory.append_to_note("test.md", "Second line")

    content = memory.read_note("test.md")
    assert "First line" in content
    assert "Second line" in content


def test_create_daily_note(temp_vault):
    """Test daily note creation."""
    memory = ObsidianMemory(temp_vault)

    daily_path = memory.create_daily_note()
    assert daily_path.startswith("daily/")
    assert daily_path.endswith(".md")

    content = memory.read_note(daily_path)
    assert "## Tasks" in content
    assert "## Notes" in content


def test_search_notes(temp_vault):
    """Test note search functionality."""
    memory = ObsidianMemory(temp_vault)

    memory.write_note("note1.md", "This contains AIM agency")
    memory.write_note("note2.md", "This is about something else")
    memory.write_note("note3.md", "AIM medical marketing")

    results = memory.search_notes("AIM")
    assert len(results) == 2
