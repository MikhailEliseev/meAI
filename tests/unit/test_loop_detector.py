"""Tests for Loop Detector"""

import pytest
from datetime import datetime, timedelta, timezone
from meai.safety.loop_detector import LoopDetector


def test_track_delegation():
    """Test tracking delegation chain"""
    detector = LoopDetector(max_depth=5)

    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")

    assert detector.get_depth("agent-3") == 3
    chain = detector.get_chain("agent-3")
    assert chain == ["agent-1", "agent-2", "agent-3"]


def test_detect_max_depth_exceeded():
    """Test detecting max delegation depth exceeded"""
    detector = LoopDetector(max_depth=3)

    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")

    # Should raise error when trying to add 4th agent (exceeds max_depth=3)
    with pytest.raises(RuntimeError, match="Max delegation depth"):
        detector.track_delegation("agent-3", "agent-4")


def test_detect_circular_delegation():
    """Test detecting circular delegation loops"""
    detector = LoopDetector()

    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")

    # Try to create circular loop
    with pytest.raises(RuntimeError, match="Circular delegation"):
        detector.track_delegation("agent-3", "agent-1")


def test_detect_self_calls():
    """Test detecting excessive self-calls"""
    detector = LoopDetector(max_self_calls=2)

    detector.track_delegation("agent-1", "agent-1")
    detector.track_delegation("agent-1", "agent-1")

    # Third self-call should fail
    with pytest.raises(RuntimeError, match="called itself"):
        detector.track_delegation("agent-1", "agent-1")


def test_reset_agent():
    """Test resetting tracking for agent"""
    detector = LoopDetector()

    detector.track_delegation("agent-1", "agent-2")
    assert detector.get_depth("agent-2") == 2

    detector.reset_agent("agent-2")
    assert detector.get_depth("agent-2") == 0


def test_cleanup_old_chains():
    """Test cleaning up old delegation chains"""
    detector = LoopDetector()

    detector.track_delegation("agent-1", "agent-2")

    # Manually set old timestamp
    detector.timestamps["agent-2"] = datetime.now(timezone.utc) - timedelta(hours=2)

    # Cleanup
    detector.cleanup_old_chains(max_age=timedelta(hours=1))

    assert detector.get_depth("agent-2") == 0


def test_get_chain():
    """Test getting delegation chain"""
    detector = LoopDetector()

    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")
    detector.track_delegation("agent-3", "agent-4")

    chain = detector.get_chain("agent-4")
    assert chain == ["agent-1", "agent-2", "agent-3", "agent-4"]


def test_independent_chains():
    """Test independent delegation chains don't interfere"""
    detector = LoopDetector()

    # Chain 1
    detector.track_delegation("agent-1", "agent-2")
    detector.track_delegation("agent-2", "agent-3")

    # Chain 2 (independent)
    detector.track_delegation("agent-4", "agent-5")

    assert detector.get_depth("agent-3") == 3
    assert detector.get_depth("agent-5") == 2
    assert detector.get_chain("agent-3") == ["agent-1", "agent-2", "agent-3"]
    assert detector.get_chain("agent-5") == ["agent-4", "agent-5"]
