"""Tests for Prompt Generator"""

import pytest
from meai.agents.prompt_generator import PromptGenerator


def test_generate_basic_prompt():
    """Test generating basic agent prompt"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
        vault_path="/vault/seo-agent",
    )

    assert prompt is not None
    assert "seo-agent" in prompt
    assert "SEO specialist" in prompt
    assert "/vault/seo-agent" in prompt


def test_prompt_includes_vault_path():
    """Test prompt includes vault path for memory access"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
        vault_path="/vault/test-agent",
    )

    assert "/vault/test-agent" in prompt
    assert "vault" in prompt.lower() or "memory" in prompt.lower()


def test_prompt_includes_role_context():
    """Test prompt includes role and department context"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="content-agent",
        agent_type="subagent",
        department="content",
        role="Content writer and editor",
        vault_path="/vault/content-agent",
    )

    assert "content" in prompt.lower()
    assert "Content writer and editor" in prompt


def test_prompt_customization():
    """Test prompt can be customized with additional context"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="ads-agent",
        agent_type="subagent",
        department="ads",
        role="Ads manager",
        vault_path="/vault/ads-agent",
        custom_instructions="Focus on Google Ads and Facebook Ads campaigns.",
    )

    assert "Google Ads" in prompt
    assert "Facebook Ads" in prompt


def test_operator_vs_subagent_prompts():
    """Test different prompts for operator vs subagent"""
    generator = PromptGenerator()

    operator_prompt = generator.generate(
        agent_id="operator",
        agent_type="operator",
        department="operations",
        role="Operations director",
        vault_path="/vault/operator",
    )

    subagent_prompt = generator.generate(
        agent_id="seo-agent",
        agent_type="subagent",
        department="seo",
        role="SEO specialist",
        vault_path="/vault/seo-agent",
    )

    # Operator should have orchestration context
    assert "orchestrat" in operator_prompt.lower() or "coordinat" in operator_prompt.lower()

    # Subagent should have task execution context
    assert "task" in subagent_prompt.lower() or "execut" in subagent_prompt.lower()


def test_prompt_template_variables():
    """Test all template variables are replaced"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
        vault_path="/vault/test-agent",
    )

    # Should not contain unreplaced template variables
    assert "{{" not in prompt
    assert "}}" not in prompt
    assert "{agent_id}" not in prompt
    assert "{role}" not in prompt


def test_prompt_length():
    """Test generated prompt has reasonable length"""
    generator = PromptGenerator()

    prompt = generator.generate(
        agent_id="test-agent",
        agent_type="subagent",
        department="test",
        role="Tester",
        vault_path="/vault/test-agent",
    )

    # Should be substantial but not too long
    assert len(prompt) > 100  # At least 100 characters
    assert len(prompt) < 5000  # Less than 5000 characters
