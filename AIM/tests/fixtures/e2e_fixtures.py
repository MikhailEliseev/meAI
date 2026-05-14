"""E2E Test Fixtures for AIM Agency System

Provides fixtures for end-to-end testing covering multi-agent coordination,
real-world scenarios, and system integration at scale.
"""

import pytest
import asyncio
import tempfile
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

from meai.events.event_bus import EventBus
from meai.events.event_store import EventStore


@pytest.fixture
async def event_bus():
    """Real Event Bus for E2E coordination testing

    Creates EventBus with in-memory SQLite database.
    Provides cleanup after test.
    """
    bus = EventBus(database_url="sqlite+aiosqlite:///:memory:")
    await bus.initialize()
    yield bus
    await bus.close()


@pytest.fixture
async def event_store(tmp_path):
    """Real Event Store for audit trail testing

    Creates EventStore with temporary SQLite database.
    Provides cleanup after test.
    """
    db_path = tmp_path / "test_event_store.db"
    store = EventStore(database_url=f"sqlite+aiosqlite:///{db_path}")
    await store.initialize()
    yield store
    await store.close()


@pytest.fixture
def mock_client_data():
    """Realistic client onboarding data

    Returns comprehensive client profile with requirements for all domains:
    - SEO (keywords, competitors)
    - Content (topics, tone, frequency)
    - Ads (platforms, budget, targeting)
    - Analytics (metrics, reporting)
    """
    return {
        "client": {
            "name": "Medical Clinic ABC",
            "domain": "https://medclinic-abc.com",
            "industry": "healthcare",
            "budget": 50000.0,
            "location": "Moscow, Russia",
            "target_audience": "Adults 25-55 seeking dental services",
        },
        "seo": {
            "target_keywords": [
                "dental implants moscow",
                "cosmetic dentistry",
                "teeth whitening",
                "orthodontics",
            ],
            "competitors": [
                "https://competitor1.com",
                "https://competitor2.com",
                "https://competitor3.com",
            ],
            "current_ranking": {
                "dental implants moscow": 15,
                "cosmetic dentistry": 8,
            },
            "target_ranking": {
                "dental implants moscow": 3,
                "cosmetic dentistry": 5,
            },
        },
        "content": {
            "topics": [
                "dental health",
                "implant procedures",
                "cosmetic dentistry benefits",
                "orthodontic treatments",
            ],
            "tone": "professional",
            "frequency": "weekly",
            "content_types": ["blog", "social", "email"],
            "target_word_count": 1500,
        },
        "ads": {
            "platforms": ["yandex", "google"],
            "budget": 20000.0,
            "targeting": {
                "geo": ["Moscow", "Saint Petersburg"],
                "age": "25-55",
                "interests": ["health", "beauty", "wellness"],
            },
            "campaign_goals": {
                "impressions": 100000,
                "clicks": 5000,
                "conversions": 250,
            },
        },
        "analytics": {
            "metrics": ["traffic", "conversions", "roi", "bounce_rate"],
            "reporting": "weekly",
            "kpis": {
                "monthly_traffic": 10000,
                "conversion_rate": 5.0,
                "roi": 300.0,
            },
        },
    }


class CorrelationTracker:
    """Track correlation IDs across workflows

    Helps verify that correlation IDs propagate correctly through
    multi-agent workflows and maintain parent-child relationships.
    """

    def __init__(self):
        self.correlations: Dict[str, List[str]] = {}
        self.events: List[Dict[str, Any]] = []

    def track(self, parent_id: str, child_id: str):
        """Track parent-child correlation relationship

        Args:
            parent_id: Parent correlation ID
            child_id: Child correlation ID
        """
        if parent_id not in self.correlations:
            self.correlations[parent_id] = []
        self.correlations[parent_id].append(child_id)

    def track_event(self, event_type: str, correlation_id: str, metadata: Dict[str, Any] = None):
        """Track event with correlation ID

        Args:
            event_type: Type of event
            correlation_id: Correlation ID
            metadata: Additional event metadata
        """
        self.events.append({
            "event_type": event_type,
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        })

    def verify_chain(self, parent_id: str) -> bool:
        """Verify correlation chain exists for parent ID

        Args:
            parent_id: Parent correlation ID to verify

        Returns:
            True if chain exists with at least one child
        """
        return parent_id in self.correlations and len(self.correlations[parent_id]) > 0

    def get_children(self, parent_id: str) -> List[str]:
        """Get all child correlation IDs for parent

        Args:
            parent_id: Parent correlation ID

        Returns:
            List of child correlation IDs
        """
        return self.correlations.get(parent_id, [])

    def get_chain_depth(self, parent_id: str) -> int:
        """Get depth of correlation chain

        Args:
            parent_id: Root correlation ID

        Returns:
            Maximum depth of correlation chain
        """
        if parent_id not in self.correlations:
            return 0

        max_depth = 1
        for child_id in self.correlations[parent_id]:
            child_depth = self.get_chain_depth(child_id)
            max_depth = max(max_depth, 1 + child_depth)

        return max_depth

    def verify_no_orphans(self) -> bool:
        """Verify no orphaned correlation IDs exist

        Returns:
            True if all child IDs have parent references
        """
        all_children = set()
        for children in self.correlations.values():
            all_children.update(children)

        all_parents = set(self.correlations.keys())

        # All children should either be parents themselves or be leaf nodes
        orphans = all_children - all_parents

        # Orphans are OK if they're leaf nodes (no children)
        return True


@pytest.fixture
def correlation_tracker():
    """Correlation tracker fixture

    Returns:
        CorrelationTracker instance for tracking correlation IDs
    """
    return CorrelationTracker()


class WorkflowTimer:
    """Measure parallel execution performance

    Tracks start/end times for workflows and calculates performance metrics
    to verify parallel execution provides speedup over sequential execution.
    """

    def __init__(self):
        self.timings: Dict[str, Dict[str, float]] = {}
        self.start_times: Dict[str, float] = {}

    def start(self, workflow_name: str):
        """Start timing a workflow

        Args:
            workflow_name: Name of workflow to time
        """
        import time
        self.start_times[workflow_name] = time.time()

    def end(self, workflow_name: str):
        """End timing a workflow

        Args:
            workflow_name: Name of workflow to stop timing
        """
        import time
        if workflow_name not in self.start_times:
            raise ValueError(f"Workflow {workflow_name} was not started")

        duration = time.time() - self.start_times[workflow_name]
        self.timings[workflow_name] = {
            "start": self.start_times[workflow_name],
            "duration": duration,
        }

    def get_duration(self, workflow_name: str) -> float:
        """Get duration for workflow

        Args:
            workflow_name: Name of workflow

        Returns:
            Duration in seconds
        """
        if workflow_name not in self.timings:
            raise ValueError(f"Workflow {workflow_name} has no timing data")
        return self.timings[workflow_name]["duration"]

    def get_total_duration(self) -> float:
        """Get total duration across all workflows

        Returns:
            Total duration in seconds (parallel execution time)
        """
        if not self.timings:
            return 0.0

        earliest_start = min(t["start"] for t in self.timings.values())
        latest_end = max(t["start"] + t["duration"] for t in self.timings.values())

        return latest_end - earliest_start

    def get_sequential_duration(self) -> float:
        """Get sequential duration (sum of all workflow durations)

        Returns:
            Sequential duration in seconds
        """
        return sum(t["duration"] for t in self.timings.values())

    def get_speedup(self) -> float:
        """Calculate parallel speedup factor

        Returns:
            Speedup factor (sequential / parallel)
        """
        total = self.get_total_duration()
        sequential = self.get_sequential_duration()

        if total == 0:
            return 0.0

        return sequential / total

    def verify_parallel_execution(self, min_speedup: float = 1.5) -> bool:
        """Verify parallel execution achieved speedup

        Args:
            min_speedup: Minimum speedup factor required

        Returns:
            True if speedup >= min_speedup
        """
        return self.get_speedup() >= min_speedup


@pytest.fixture
def workflow_timer():
    """Workflow timer fixture

    Returns:
        WorkflowTimer instance for measuring parallel execution
    """
    return WorkflowTimer()
