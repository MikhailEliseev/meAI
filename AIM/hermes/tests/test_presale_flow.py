"""Validate PRESALE conversation flow consistency between SOUL.md and agent_wrapper.py.

These are content/string assertion tests — no mocking, no external deps.
They verify that the PRESALE flow is step-by-step (not parallel-first),
conversational in tone, and consistent across both files.
"""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SOUL_PATH = PROJECT_ROOT / "AIM" / "hermes" / "skills" / "aim" / "SOUL.md"
HERMES_APP = PROJECT_ROOT / "AIM" / "hermes" / "app"


@pytest.fixture(scope="module")
def soul_md():
    if not SOUL_PATH.exists():
        pytest.skip(f"SOUL.md not found at {SOUL_PATH}")
    return SOUL_PATH.read_text()


@pytest.fixture(scope="module")
def presale_section(soul_md):
    lines = soul_md.split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.startswith("### PRESALE"):
            start = i
            break
    if start is None:
        pytest.skip("PRESALE section not found in SOUL.md")
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("### ") and not lines[i].startswith("#### "):
            end = i
            break
    return "\n".join(lines[start:end])


@pytest.fixture(scope="module")
def presale_prompt():
    """Extract _presale_prompt() return string from agent_wrapper.py source.

    We parse the source directly because agent_wrapper imports hermes_state
    (a Docker-only dependency not available in local venv).
    """
    import re
    agent_wrapper_path = HERMES_APP / "agent_wrapper.py"
    if not agent_wrapper_path.exists():
        pytest.skip(f"agent_wrapper.py not found at {agent_wrapper_path}")
    source = agent_wrapper_path.read_text()

    # Find the _presale_prompt function's triple-quoted return string
    # Pattern: def _presale_prompt(): ... return """..."""
    match = re.search(
        r'def _presale_prompt\(\)[^:]*:\s*\n\s*""".*?\n\s*""".*?"""(.*?)"""',
        source, re.DOTALL
    )
    if match:
        return match.group(1).strip()

    # Fallback: find the return """ block
    match = re.search(
        r'def _presale_prompt\(\)[^:]*:.*?return\s+"""(.*?)"""',
        source, re.DOTALL
    )
    if match:
        return match.group(1).strip()

    pytest.skip("Could not extract _presale_prompt() return value from agent_wrapper.py")


# ── SOUL.md tests ────────────────────────────────────────────────────────

def test_presale_section_has_eight_steps(presale_section):
    """SOUL.md PRESALE section contains Шаг 1 through Шаг 8 in sequential order."""
    for step_num in range(1, 9):
        step_marker = f"Шаг {step_num}"
        assert step_marker in presale_section, f"Missing: {step_marker}"


def test_presale_section_no_parallel_first(presale_section):
    """SOUL.md PRESALE section does NOT contain old parallel-first instructions."""
    assert "запускаю ВСЕ нужные инструменты ОДНОВРЕМЕННО" not in presale_section
    assert "ВСЕГДА параллельно" not in presale_section


def test_presale_section_has_conversational_phrases(presale_section):
    """SOUL.md PRESALE section contains at least 2 conversational markers."""
    markers = [
        "Скиньте",
        "Ага",
        "смотрите",
        "как будто друг",
        "живой диалог",
        "не машина",
        "ЖИВОЙ ДИАЛОГ",
    ]
    found = sum(1 for m in markers if m.lower() in presale_section.lower())
    assert found >= 2, f"Only {found}/7 conversational markers found"


def test_presale_section_has_report_parts(presale_section):
    """SOUL.md PRESALE section has both friendly and detailed report parts."""
    has_part1 = any(phrase in presale_section for phrase in [
        "Часть 1", "ЧАСТЬ 1", "Дружеские выводы",
        "свободная форма", "свободный разговорный",
    ])
    has_part2 = any(phrase in presale_section for phrase in [
        "Часть 2", "ЧАСТЬ 2", "Детальный разбор",
        "структурированный детальный",
    ])
    assert has_part1, "Missing: friendly summary part (Часть 1)"
    assert has_part2, "Missing: detailed breakdown part (Часть 2)"


# ── agent_wrapper.py tests ───────────────────────────────────────────────

def test_presale_prompt_no_parallel_first(presale_prompt):
    """_presale_prompt() does NOT contain old parallel-first instructions."""
    assert "ОДНОВРЕМЕННО" not in presale_prompt
    assert "ВСЕГДА параллельно" not in presale_prompt


def test_presale_prompt_has_step_by_step(presale_prompt):
    """_presale_prompt() contains step-by-step dialogue guidance."""
    step_markers = ["шаг", "пошагов", "диалог", "живой", "ЖИВОЙ"]
    found = any(m.lower() in presale_prompt.lower() for m in step_markers)
    assert found, "Missing: step-by-step dialogue language in _presale_prompt()"


def test_presale_prompt_retains_principles(presale_prompt):
    """_presale_prompt() retains core principles after rewrite."""
    principles = [
        "Цифры из инструментов",
        "Бизнес-язык",
        "Контакт",
    ]
    for principle in principles:
        assert principle in presale_prompt, f"Lost core principle: {principle}"


# ── Cross-file consistency tests ────────────────────────────────────────

def test_mode_prompt_and_soul_consistent(presale_section, presale_prompt):
    """Both SOUL.md and _presale_prompt() agree on the new conversational flow."""
    both = [presale_section.lower(), presale_prompt.lower()]

    # Neither file should have old parallel-first patterns
    old_patterns = [
        "запускаю все нужные инструменты одновременно",
        "всегда параллельно",
    ]
    for i, text in enumerate(both):
        label = ["SOUL.md", "agent_wrapper.py"][i]
        for pattern in old_patterns:
            assert pattern not in text, f"Old pattern '{pattern}' still in {label}"

    # Both should have step-by-step guidance
    for text in both:
        has_step = any(m in text for m in ["шаг", "пошагов", "диалог", "живой"])
        assert has_step, "Step-by-step guidance missing in one of the files"

    # Both should have friendly-first report format
    for text in both:
        has_friendly = any(m in text for m in ["сначала", "дружеск", "разговорный вывод"])
        assert has_friendly, "Friendly-first report format missing in one of the files"
