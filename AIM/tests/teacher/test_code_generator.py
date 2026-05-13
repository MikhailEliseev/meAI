# AIM/tests/teacher/test_code_generator.py
import pytest
from AIM.src.aim.teacher.code_generator import CodeGenerator
from AIM.src.aim.teacher.pattern_extractor import ExtractedPattern


def test_add_imports():
    """Test adding imports to code."""
    original = """
import requests

class Client:
    pass
"""

    pattern = ExtractedPattern(
        name="circuit_breaker",
        code="",
        imports=["from pybreaker import CircuitBreaker"],
        parameters={},
        description="",
    )

    generator = CodeGenerator()
    updated = generator.add_imports(original, pattern)

    assert "from pybreaker import CircuitBreaker" in updated
    assert "import requests" in updated


def test_add_to_init():
    """Test adding code to __init__ method."""
    original = """
class Client:
    def __init__(self):
        self.url = "http://example.com"
"""

    pattern = ExtractedPattern(
        name="circuit_breaker",
        code="self.breaker = CircuitBreaker(fail_max=5)",
        imports=[],
        parameters={},
        description="",
    )

    generator = CodeGenerator()
    updated = generator.add_to_init(original, pattern)

    assert "self.breaker = CircuitBreaker(fail_max=5)" in updated
    assert "self.url" in updated
