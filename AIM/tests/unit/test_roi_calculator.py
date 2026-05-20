"""Tests for ROI calculator."""
import pytest
from aim.subagents.ads.roi_calculator import ROICalculator, ChannelROI


@pytest.fixture
def calc():
    return ROICalculator()


def test_roas_calculation(calc):
    """ROAS = Revenue / Cost."""
    assert calc.calculate_roas(cost=5000.0, revenue=25000.0) == 5.0
    assert calc.calculate_roas(cost=1000.0, revenue=500.0) == 0.5
    assert calc.calculate_roas(cost=0.0, revenue=1000.0) == 0.0


def test_roi_calculation(calc):
    """ROI = (Revenue - Cost) / Cost."""
    assert calc.calculate_roi(cost=5000.0, revenue=25000.0) == 4.0
    assert calc.calculate_roi(cost=1000.0, revenue=500.0) == -0.5
    assert calc.calculate_roi(cost=0.0, revenue=1000.0) == 0.0


def test_channel_breakdown(calc):
    """Multiple channels produce correct per-channel ROAS/ROI."""
    data = [
        {"channel": "yandex", "cost": 10000.0, "revenue": 50000.0, "conversions": 5},
        {"channel": "vk", "cost": 5000.0, "revenue": 10000.0, "conversions": 2},
        {"channel": "telegram", "cost": 3000.0, "revenue": 9000.0, "conversions": 1},
    ]
    channels = calc.channel_breakdown(data)
    assert len(channels) == 3
    assert channels[0].channel == "yandex"
    assert channels[0].roas == 5.0
    assert channels[0].roi == 4.0
    assert channels[1].channel == "vk"
    assert channels[1].roas == 2.0
    assert channels[1].roi == 1.0
    assert channels[2].channel == "telegram"
    assert channels[2].roas == 3.0
    assert channels[2].roi == 2.0


def test_generate_report(calc):
    """generate_report returns CampaignROIReport with aggregated totals."""
    data = [
        {"channel": "yandex", "cost": 10000.0, "revenue": 40000.0, "conversions": 4},
        {"channel": "vk", "cost": 5000.0, "revenue": 15000.0, "conversions": 3},
    ]
    report = calc.generate_report(data)
    assert report.total_cost == 15000.0
    assert report.total_revenue == 55000.0
    assert report.overall_roas == pytest.approx(3.67, rel=0.01)
    assert report.overall_roi == pytest.approx(2.67, rel=0.01)
    assert len(report.channels) == 2


def test_empty_channel_data(calc):
    """Empty input produces empty report."""
    report = calc.generate_report([])
    assert report.total_cost == 0.0
    assert report.total_revenue == 0.0
    assert report.overall_roas == 0.0
    assert report.channels == []
