"""Tests for Context Monitor"""

import pytest
from meai.safety.context_monitor import ContextMonitor


def test_context_usage_tracking():
    """Test tracking context usage"""
    monitor = ContextMonitor(max_tokens=100000, warning_threshold=0.4)

    # Track usage
    monitor.track_usage(30000)
    assert monitor.get_usage_percent() == 0.3

    # Update to higher usage
    monitor.track_usage(45000)
    assert monitor.get_usage_percent() == 0.45

    # Should trigger warning
    assert monitor.should_warn()


def test_should_compact():
    """Test auto-compact trigger"""
    monitor = ContextMonitor(max_tokens=100000, critical_threshold=0.5)

    monitor.track_usage(40000)
    assert not monitor.should_compact()

    monitor.track_usage(55000)
    assert monitor.should_compact()


def test_reset():
    """Test resetting tracking"""
    monitor = ContextMonitor(max_tokens=100000)

    monitor.track_usage(50000)
    assert monitor.current_tokens == 50000

    monitor.reset()
    assert monitor.current_tokens == 0
    assert not monitor.warned


def test_get_status():
    """Test getting current status"""
    monitor = ContextMonitor(max_tokens=100000)

    monitor.track_usage(30000)
    status = monitor.get_status()

    assert status["status"] == "ok"
    assert status["current_tokens"] == 30000
    assert status["usage_percent"] == 0.3
    assert status["remaining_tokens"] == 70000

    monitor.track_usage(45000)
    status = monitor.get_status()
    assert status["status"] == "warning"

    monitor.track_usage(55000)
    status = monitor.get_status()
    assert status["status"] == "critical"


def test_get_remaining_tokens():
    """Test getting remaining tokens"""
    monitor = ContextMonitor(max_tokens=100000)

    monitor.track_usage(30000)
    assert monitor.get_remaining_tokens() == 70000

    monitor.track_usage(80000)
    assert monitor.get_remaining_tokens() == 20000


def test_warning_threshold():
    """Test warning threshold detection"""
    monitor = ContextMonitor(max_tokens=100000, warning_threshold=0.4)

    monitor.track_usage(30000)
    assert not monitor.should_warn()

    monitor.track_usage(40000)
    assert monitor.should_warn()


def test_critical_threshold():
    """Test critical threshold detection"""
    monitor = ContextMonitor(max_tokens=100000, critical_threshold=0.5)

    monitor.track_usage(40000)
    assert not monitor.should_compact()

    monitor.track_usage(50000)
    assert monitor.should_compact()


def test_custom_thresholds():
    """Test custom warning and critical thresholds"""
    monitor = ContextMonitor(
        max_tokens=100000,
        warning_threshold=0.6,
        critical_threshold=0.8,
    )

    monitor.track_usage(50000)
    assert not monitor.should_warn()

    monitor.track_usage(65000)
    assert monitor.should_warn()
    assert not monitor.should_compact()

    monitor.track_usage(85000)
    assert monitor.should_compact()


def test_warned_flag():
    """Test warned flag is set after warning"""
    monitor = ContextMonitor(max_tokens=100000, warning_threshold=0.4)

    assert not monitor.warned

    monitor.track_usage(45000)
    assert monitor.warned

    # Reset clears warned flag
    monitor.reset()
    assert not monitor.warned
