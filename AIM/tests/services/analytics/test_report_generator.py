"""Tests for ReportGenerator

Part of: Phase 11 Sprint 2 - Task 2.5
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.aim.schemas.analytics import (
    ConversionFunnel,
    EmailMetrics,
    LeadMetrics,
    RealTimeStats,
    TimeSeriesPoint,
)
from src.aim.services.analytics.report_generator import ReportGenerator


@pytest.fixture
def sample_lead_metrics():
    """Sample lead metrics for testing."""
    now = datetime.utcnow()
    return LeadMetrics(
        total_leads=100,
        leads_by_tier={"hot": 30, "warm": 50, "cold": 20},
        leads_by_source={"landing_page": 60, "referral": 25, "organic": 15},
        leads_by_specialty={"dentist": 40, "therapist": 35, "surgeon": 25},
        average_score=65.5,
        capture_rate=5.2,
        duplicate_rate=3.5,
        time_series=[
            TimeSeriesPoint(
                timestamp=now - timedelta(days=i),
                value=10 + i,
                label=f"Day {i}",
            )
            for i in range(7)
        ],
        start_date=now - timedelta(days=7),
        end_date=now,
        generated_at=now,
    )


@pytest.fixture
def sample_email_metrics():
    """Sample email metrics for testing."""
    now = datetime.utcnow()
    return EmailMetrics(
        total_sent=500,
        total_scheduled=50,
        total_failed=10,
        total_delivered=490,
        total_opened=245,
        total_clicked=98,
        total_bounced=5,
        total_complained=2,
        total_unsubscribed=3,
        delivery_rate=98.0,
        open_rate=50.0,
        click_rate=40.0,
        bounce_rate=1.0,
        complaint_rate=0.4,
        unsubscribe_rate=0.6,
        emails_by_tier={"hot": 150, "warm": 250, "cold": 100},
        avg_time_to_open=15.5,
        avg_time_to_click=25.3,
        time_series=[
            TimeSeriesPoint(
                timestamp=now - timedelta(days=i),
                value=50 + i * 5,
                label=f"Day {i}",
            )
            for i in range(7)
        ],
        start_date=now - timedelta(days=7),
        end_date=now,
        generated_at=now,
    )


@pytest.fixture
def sample_conversion_funnel():
    """Sample conversion funnel for testing."""
    now = datetime.utcnow()
    return ConversionFunnel(
        leads_captured=100,
        leads_scored=95,
        tasks_created=30,
        workflows_triggered=95,
        emails_sent=500,
        emails_delivered=490,
        emails_opened=245,
        emails_clicked=98,
        conversion_rates={
            "capture_to_score": 95.0,
            "score_to_task": 31.6,
            "task_to_workflow": 100.0,
            "workflow_to_sent": 90.0,
            "sent_to_delivered": 98.0,
            "delivered_to_opened": 50.0,
            "opened_to_clicked": 40.0,
        },
        start_date=now - timedelta(days=7),
        end_date=now,
        generated_at=now,
    )


@pytest.fixture
def sample_realtime_stats():
    """Sample real-time stats for testing."""
    return RealTimeStats(
        leads_today=15,
        emails_sent_today=75,
        emails_opened_today=30,
        emails_clicked_today=12,
        active_workflows=85,
        pending_emails=25,
        hot_leads_count=30,
        hot_leads_today=5,
        last_updated=datetime.utcnow(),
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for reports."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def report_generator(temp_output_dir):
    """ReportGenerator instance with temp directory."""
    return ReportGenerator(output_dir=temp_output_dir)


class TestReportGenerator:
    """Test suite for ReportGenerator."""

    def test_csv_report_generation(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test CSV report generation."""
        file_path = report_generator.generate_csv_report(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        # Check file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".csv")

        # Check file content
        with open(file_path, "r") as f:
            content = f.read()
            assert "Analytics Report" in content
            assert "LEAD METRICS" in content
            assert "EMAIL METRICS" in content
            assert "CONVERSION FUNNEL" in content
            assert str(sample_lead_metrics.total_leads) in content
            assert str(sample_email_metrics.total_sent) in content

    def test_json_report_generation(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
        sample_realtime_stats: RealTimeStats,
    ):
        """Test JSON report generation."""
        file_path = report_generator.generate_json_report(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
            realtime_stats=sample_realtime_stats,
        )

        # Check file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".json")

        # Check file content
        with open(file_path, "r") as f:
            data = json.load(f)
            assert "generated_at" in data
            assert "period" in data
            assert "lead_metrics" in data
            assert "email_metrics" in data
            assert "conversion_funnel" in data
            assert "realtime_stats" in data
            assert data["lead_metrics"]["total_leads"] == 100
            assert data["email_metrics"]["total_sent"] == 500

    def test_pdf_report_generation(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test PDF report generation."""
        file_path = report_generator.generate_pdf_report(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
            include_charts=False,
        )

        # Check file exists
        assert os.path.exists(file_path)
        assert file_path.endswith(".pdf")

        # Check file size (PDF should be non-empty)
        file_size = os.path.getsize(file_path)
        assert file_size > 1000  # At least 1KB

    def test_csv_report_content_structure(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test CSV report has correct structure."""
        file_path = report_generator.generate_csv_report(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        with open(file_path, "r") as f:
            lines = f.readlines()

        # Check sections exist
        content = "".join(lines)
        assert "Leads by Tier" in content
        assert "Leads by Source" in content
        assert "Conversion Rates" in content

    def test_json_report_structure(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
        sample_realtime_stats: RealTimeStats,
    ):
        """Test JSON report has correct structure."""
        file_path = report_generator.generate_json_report(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
            realtime_stats=sample_realtime_stats,
        )

        with open(file_path, "r") as f:
            data = json.load(f)

        # Check nested structure
        assert "leads_by_tier" in data["lead_metrics"]
        assert "leads_by_source" in data["lead_metrics"]
        assert "emails_by_tier" in data["email_metrics"]
        assert "conversion_rates" in data["conversion_funnel"]

    def test_recommendations_low_capture_rate(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test recommendations for low capture rate."""
        # Set low capture rate
        sample_lead_metrics.capture_rate = 2.0

        recommendations = report_generator._generate_recommendations(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        assert any("capture rate" in rec.lower() for rec in recommendations)

    def test_recommendations_high_duplicate_rate(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test recommendations for high duplicate rate."""
        # Set high duplicate rate
        sample_lead_metrics.duplicate_rate = 15.0

        recommendations = report_generator._generate_recommendations(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        assert any("duplicate" in rec.lower() for rec in recommendations)

    def test_recommendations_low_open_rate(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test recommendations for low open rate."""
        # Set low open rate
        sample_email_metrics.open_rate = 15.0

        recommendations = report_generator._generate_recommendations(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        assert any("open rate" in rec.lower() for rec in recommendations)

    def test_recommendations_all_good(
        self,
        report_generator: ReportGenerator,
        sample_lead_metrics: LeadMetrics,
        sample_email_metrics: EmailMetrics,
        sample_conversion_funnel: ConversionFunnel,
    ):
        """Test recommendations when all metrics are good."""
        recommendations = report_generator._generate_recommendations(
            lead_metrics=sample_lead_metrics,
            email_metrics=sample_email_metrics,
            funnel=sample_conversion_funnel,
        )

        # Should have at least one recommendation (even if all good)
        assert len(recommendations) > 0

    def test_output_directory_creation(self, tmp_path):
        """Test output directory is created if it doesn't exist."""
        output_dir = tmp_path / "new_reports"
        generator = ReportGenerator(output_dir=str(output_dir))

        assert output_dir.exists()
        assert output_dir.is_dir()
