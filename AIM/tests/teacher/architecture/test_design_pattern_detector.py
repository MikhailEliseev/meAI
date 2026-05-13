"""
Tests for DesignPatternDetector.

Tests:
- Design pattern detection (Strategy, Factory, Observer, Singleton, DI)
- Architecture style identification (Layered, Hexagonal, Clean)
- SOLID principles compliance checking
"""

from pathlib import Path

import pytest

from AIM.src.aim.teacher.architecture.design_pattern_detector import (
    DesignPatternDetector,
    DesignPatterns,
)


@pytest.fixture
def detector():
    """Create DesignPatternDetector instance."""
    return DesignPatternDetector()


@pytest.fixture
def strategy_pattern_repo(tmp_path):
    """Create repo with Strategy pattern."""
    repo = tmp_path / "strategy_repo"
    repo.mkdir()

    # Strategy interface
    (repo / "payment_strategy.py").write_text("""
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass
""")

    # Concrete strategies
    (repo / "credit_card_strategy.py").write_text("""
from payment_strategy import PaymentStrategy

class CreditCardStrategy(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        return True
""")

    (repo / "paypal_strategy.py").write_text("""
from payment_strategy import PaymentStrategy

class PayPalStrategy(PaymentStrategy):
    def pay(self, amount: float) -> bool:
        return True
""")

    return repo


@pytest.fixture
def factory_pattern_repo(tmp_path):
    """Create repo with Factory pattern."""
    repo = tmp_path / "factory_repo"
    repo.mkdir()

    (repo / "animal_factory.py").write_text("""
class Animal:
    pass

class Dog(Animal):
    pass

class Cat(Animal):
    pass

class AnimalFactory:
    @staticmethod
    def create_animal(animal_type: str) -> Animal:
        if animal_type == "dog":
            return Dog()
        elif animal_type == "cat":
            return Cat()
        raise ValueError(f"Unknown animal type: {animal_type}")
""")

    return repo


@pytest.fixture
def observer_pattern_repo(tmp_path):
    """Create repo with Observer pattern."""
    repo = tmp_path / "observer_repo"
    repo.mkdir()

    (repo / "event_manager.py").write_text("""
class EventManager:
    def __init__(self):
        self._listeners = []

    def subscribe(self, listener):
        self._listeners.append(listener)

    def notify(self, event):
        for listener in self._listeners:
            listener.update(event)
""")

    return repo


@pytest.fixture
def singleton_pattern_repo(tmp_path):
    """Create repo with Singleton pattern."""
    repo = tmp_path / "singleton_repo"
    repo.mkdir()

    (repo / "database.py").write_text("""
class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
""")

    return repo


@pytest.fixture
def dependency_injection_repo(tmp_path):
    """Create repo with Dependency Injection."""
    repo = tmp_path / "di_repo"
    repo.mkdir()

    (repo / "service.py").write_text("""
class Service:
    def __init__(self, repository, logger):
        self.repository = repository
        self.logger = logger
""")

    return repo


@pytest.fixture
def layered_architecture_repo(tmp_path):
    """Create repo with Layered architecture."""
    repo = tmp_path / "layered_repo"
    repo.mkdir()

    # Presentation layer
    presentation = repo / "presentation"
    presentation.mkdir()
    (presentation / "api.py").write_text("# API layer")

    # Business layer
    business = repo / "business"
    business.mkdir()
    (business / "service.py").write_text("# Business logic")

    # Data layer
    data = repo / "data"
    data.mkdir()
    (data / "repository.py").write_text("# Data access")

    return repo


class TestPatternDetection:
    """Test design pattern detection."""

    @pytest.mark.asyncio
    async def test_detect_strategy_pattern(self, detector, strategy_pattern_repo):
        """Should detect Strategy pattern."""
        patterns = await detector.analyze(strategy_pattern_repo)

        assert "Strategy" in patterns.patterns

    @pytest.mark.asyncio
    async def test_detect_factory_pattern(self, detector, factory_pattern_repo):
        """Should detect Factory pattern."""
        patterns = await detector.analyze(factory_pattern_repo)

        assert "Factory" in patterns.patterns

    @pytest.mark.asyncio
    async def test_detect_observer_pattern(self, detector, observer_pattern_repo):
        """Should detect Observer pattern."""
        patterns = await detector.analyze(observer_pattern_repo)

        assert "Observer" in patterns.patterns

    @pytest.mark.asyncio
    async def test_detect_singleton_pattern(self, detector, singleton_pattern_repo):
        """Should detect Singleton pattern."""
        patterns = await detector.analyze(singleton_pattern_repo)

        assert "Singleton" in patterns.patterns

    @pytest.mark.asyncio
    async def test_detect_dependency_injection(self, detector, dependency_injection_repo):
        """Should detect Dependency Injection pattern."""
        patterns = await detector.analyze(dependency_injection_repo)

        assert "Dependency Injection" in patterns.patterns

    @pytest.mark.asyncio
    async def test_detect_multiple_patterns(self, detector, tmp_path):
        """Should detect multiple patterns in same repo."""
        repo = tmp_path / "multi_pattern_repo"
        repo.mkdir()

        # Strategy pattern
        (repo / "strategy.py").write_text("""
from abc import ABC, abstractmethod

class Strategy(ABC):
    @abstractmethod
    def execute(self):
        pass

class ConcreteStrategy(Strategy):
    def execute(self):
        pass
""")

        # Factory pattern
        (repo / "factory.py").write_text("""
class Factory:
    @staticmethod
    def create(type: str):
        if type == "a":
            return A()
        return B()
""")

        patterns = await detector.analyze(repo)

        assert len(patterns.patterns) >= 2


class TestArchitectureStyleIdentification:
    """Test architecture style identification."""

    @pytest.mark.asyncio
    async def test_identify_layered_architecture(self, detector, layered_architecture_repo):
        """Should identify Layered architecture."""
        patterns = await detector.analyze(layered_architecture_repo)

        assert patterns.architecture_style == "Layered"

    @pytest.mark.asyncio
    async def test_identify_unknown_architecture(self, detector, tmp_path):
        """Should return Unknown for unclear architecture."""
        repo = tmp_path / "unclear_repo"
        repo.mkdir()
        (repo / "random.py").write_text("# Random code")

        patterns = await detector.analyze(repo)

        assert patterns.architecture_style == "Unknown"


class TestSOLIDCompliance:
    """Test SOLID principles compliance checking."""

    @pytest.mark.asyncio
    async def test_single_responsibility_principle(self, detector, tmp_path):
        """Should check Single Responsibility Principle."""
        repo = tmp_path / "srp_repo"
        repo.mkdir()

        # Good SRP: class with single responsibility
        (repo / "user_repository.py").write_text("""
class UserRepository:
    def save(self, user):
        pass

    def find(self, user_id):
        pass
""")

        patterns = await detector.analyze(repo)

        # Should detect good SRP compliance
        assert patterns.solid_compliance.get("S", False) is True

    @pytest.mark.asyncio
    async def test_open_closed_principle(self, detector, strategy_pattern_repo):
        """Should check Open/Closed Principle."""
        patterns = await detector.analyze(strategy_pattern_repo)

        # Strategy pattern supports OCP (open for extension, closed for modification)
        assert patterns.solid_compliance.get("O", False) is True

    @pytest.mark.asyncio
    async def test_dependency_inversion_principle(self, detector, dependency_injection_repo):
        """Should check Dependency Inversion Principle."""
        patterns = await detector.analyze(dependency_injection_repo)

        # DI pattern supports DIP (depend on abstractions)
        assert patterns.solid_compliance.get("D", False) is True


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_handle_empty_repo(self, detector, tmp_path):
        """Should handle empty repository."""
        empty_repo = tmp_path / "empty"
        empty_repo.mkdir()

        patterns = await detector.analyze(empty_repo)

        assert len(patterns.patterns) == 0
        assert patterns.architecture_style == "Unknown"

    @pytest.mark.asyncio
    async def test_handle_syntax_errors(self, detector, tmp_path):
        """Should handle files with syntax errors."""
        repo = tmp_path / "error_repo"
        repo.mkdir()
        (repo / "broken.py").write_text("this is not valid python")

        # Should not crash
        patterns = await detector.analyze(repo)
        assert isinstance(patterns, DesignPatterns)

    @pytest.mark.asyncio
    async def test_no_false_positives(self, detector, tmp_path):
        """Should not detect patterns where they don't exist."""
        repo = tmp_path / "simple_repo"
        repo.mkdir()
        (repo / "simple.py").write_text("""
def add(a, b):
    return a + b
""")

        patterns = await detector.analyze(repo)

        # Simple function should not trigger pattern detection
        assert len(patterns.patterns) == 0
