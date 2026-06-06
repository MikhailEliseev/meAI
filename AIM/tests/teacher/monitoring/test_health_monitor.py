"""
Tests for HealthMonitor.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.aim.teacher.monitoring.health_monitor import (
    HealthMonitor,
    EndpointStatus,
    Severity,
    EndpointHealth,
    HealthAlert,
)


@pytest.fixture
def health_monitor():
    """Create HealthMonitor instance."""
    return HealthMonitor(
        alert_threshold_warning=3,
        alert_threshold_critical=5,
        disable_threshold=10,
        check_timeout=5,
    )


@pytest.mark.asyncio
async def test_check_exa_api_healthy(health_monitor):
    """Test Exa API health check when healthy."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        health = await health_monitor.check_exa_api()

        assert health.name == "exa_api"
        assert health.status == EndpointStatus.HEALTHY
        assert health.consecutive_failures == 0
        assert health.response_time_ms is not None


@pytest.mark.asyncio
async def test_check_exa_api_failure(health_monitor):
    """Test Exa API health check when failing."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection timeout")

        health = await health_monitor.check_exa_api()

        assert health.name == "exa_api"
        assert health.status == EndpointStatus.DEGRADED
        assert health.consecutive_failures == 1
        assert health.last_error == "Connection timeout"


@pytest.mark.asyncio
async def test_check_github_api_healthy(health_monitor):
    """Test GitHub API health check when healthy."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        health = await health_monitor.check_github_api()

        assert health.name == "github_api"
        assert health.status == EndpointStatus.HEALTHY
        assert health.consecutive_failures == 0


@pytest.mark.asyncio
async def test_consecutive_failures_increment(health_monitor):
    """Test that consecutive failures increment correctly."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        # First failure
        health1 = await health_monitor.check_exa_api()
        assert health1.consecutive_failures == 1

        # Second failure
        health2 = await health_monitor.check_exa_api()
        assert health2.consecutive_failures == 2

        # Third failure
        health3 = await health_monitor.check_exa_api()
        assert health3.consecutive_failures == 3


@pytest.mark.asyncio
async def test_status_degraded_after_threshold(health_monitor):
    """Test status becomes DEGRADED after warning threshold."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        # Fail 3 times (warning threshold)
        for _ in range(3):
            health = await health_monitor.check_exa_api()

        assert health.status == EndpointStatus.DEGRADED
        assert health.consecutive_failures == 3


@pytest.mark.asyncio
async def test_status_down_after_disable_threshold(health_monitor):
    """Test status becomes DOWN after disable threshold."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        # Fail 10 times (disable threshold)
        for _ in range(10):
            health = await health_monitor.check_exa_api()

        assert health.status == EndpointStatus.DOWN
        assert health.consecutive_failures == 10


@pytest.mark.asyncio
async def test_check_all_endpoints(health_monitor):
    """Test checking all endpoints in parallel."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        results = await health_monitor.check_all_endpoints()

        assert "exa_api" in results
        assert "github_api" in results
        assert "event_bus" in results
        assert "obsidian" in results


@pytest.mark.asyncio
async def test_alert_created_at_warning_threshold(health_monitor):
    """Test alert is created at warning threshold."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        with patch.object(health_monitor, "_send_alert") as mock_send:
            # Fail 3 times to trigger warning
            for _ in range(3):
                await health_monitor.check_exa_api()

            await health_monitor._check_and_alert()

            # Alert should be sent
            assert mock_send.called
            alert = mock_send.call_args[0][0]
            assert alert.severity == Severity.WARNING
            assert alert.endpoint == "exa_api"


@pytest.mark.asyncio
async def test_alert_created_at_critical_threshold(health_monitor):
    """Test alert is created at critical threshold."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        mock_get.side_effect = Exception("Connection error")

        with patch.object(health_monitor, "_send_alert") as mock_send:
            # Fail 5 times to trigger critical
            for _ in range(5):
                await health_monitor.check_exa_api()

            await health_monitor._check_and_alert()

            # Alert should be sent
            assert mock_send.called
            alert = mock_send.call_args[0][0]
            assert alert.severity == Severity.CRITICAL
            assert alert.endpoint == "exa_api"


@pytest.mark.asyncio
async def test_alert_contains_impact_and_actions(health_monitor):
    """Test alert contains impact and action items."""
    health = EndpointHealth(
        name="exa_api",
        status=EndpointStatus.DEGRADED,
        consecutive_failures=3,
        last_error="Connection timeout",
    )

    alert = health_monitor._create_alert("exa_api", health, Severity.WARNING)

    assert alert.endpoint == "exa_api"
    assert alert.severity == Severity.WARNING
    assert alert.impact == "Cannot perform deep research"
    assert len(alert.action_items) > 0
    assert "Check Exa API status" in alert.action_items


@pytest.mark.asyncio
async def test_console_alert_format(health_monitor, capsys):
    """Test console alert formatting."""
    alert = HealthAlert(
        endpoint="exa_api",
        severity=Severity.CRITICAL,
        status=EndpointStatus.DOWN,
        consecutive_failures=5,
        error="Connection timeout",
        impact="Cannot perform deep research",
        action_items=["Check API status", "Verify API key"],
    )

    health_monitor._send_console_alert(alert)

    captured = capsys.readouterr()
    assert "🚨" in captured.out
    assert "CRITICAL" in captured.out
    assert "exa_api" in captured.out
    assert "Connection timeout" in captured.out
    assert "Cannot perform deep research" in captured.out
    assert "Check API status" in captured.out


@pytest.mark.asyncio
async def test_recovery_resets_failures(health_monitor):
    """Test that recovery resets consecutive failures."""
    with patch.object(health_monitor.http_client, "get") as mock_get:
        # First fail
        mock_get.side_effect = Exception("Connection error")
        health1 = await health_monitor.check_exa_api()
        assert health1.consecutive_failures == 1

        # Then recover
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.side_effect = None
        mock_get.return_value = mock_response

        health2 = await health_monitor.check_exa_api()
        assert health2.consecutive_failures == 0
        assert health2.status == EndpointStatus.HEALTHY


@pytest.mark.asyncio
async def test_close_http_client(health_monitor):
    """Test HTTP client is closed properly."""
    with patch.object(health_monitor.http_client, "aclose") as mock_close:
        await health_monitor.close()
        assert mock_close.called
