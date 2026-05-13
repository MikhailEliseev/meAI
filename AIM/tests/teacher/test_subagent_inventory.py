# AIM/tests/teacher/test_subagent_inventory.py
import pytest
from AIM.src.aim.teacher.subagent_inventory import SubagentInventory


def test_scan_subagents():
    """Test scanning subagents directory."""
    inventory = SubagentInventory()
    subagents = inventory.scan()

    assert len(subagents) > 0
    assert "content_writer_agent" in [s.name for s in subagents]


def test_subagent_metadata():
    """Test subagent metadata extraction."""
    inventory = SubagentInventory()
    subagents = inventory.scan()

    subagent = subagents[0]
    assert hasattr(subagent, "name")
    assert hasattr(subagent, "path")
    assert hasattr(subagent, "created_date")
    assert hasattr(subagent, "has_github_integration")
