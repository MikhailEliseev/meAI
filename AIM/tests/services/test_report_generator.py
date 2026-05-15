"""Tests for ReportGenerator service."""

import pytest
from datetime import date, timedelta
from pathlib import Path
import tempfile
import sys

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from aim.services.report_generator import ReportGenerator, ReportData


class TestReportGenerator:
    """Test ReportGenerator class."""

    def test_report_generator_initialization(self):
        """Test ReportGenerator initialization."""
        generator = ReportGenerator(
            logo_path="assets/logo.png",
            brand_color="#1E40AF"
        )

        assert generator.logo_path == "assets/logo.png"
        assert generator.brand_color == "#1E40AF"
        assert generator.styles is not None

    def test_generate_basic_report(self):
        """Test generating basic report without optional metrics."""
        generator = ReportGenerator()

        # Create test data
        report_data = ReportData(
            project_id="proj-123",
            project_name="SEO Audit - Test Client",
            client_name="Test Client",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            total_tasks=20,
            completed_tasks=12,
            in_progress_tasks=5,
            blocked_tasks=1,
            estimated_hours=80.0,
            actual_hours=45.5,
            remaining_hours=34.5,
            milestones=[
                {
                    "name": "Phase 1: Research",
                    "status": "Completed",
                    "progress": 100,
                    "due_date": "2026-05-10",
                },
                {
                    "name": "Phase 2: Implementation",
                    "status": "In Progress",
                    "progress": 60,
                    "due_date": "2026-05-20",
                },
            ],
            tasks_by_status={
                "Completed": 12,
                "In Progress": 5,
                "Blocked": 1,
                "Todo": 2,
            },
            tasks_by_assignee={
                "seo-magister": 8,
                "keyword-research-agent": 6,
                "content-gap-agent": 6,
            },
        )

        # Generate report
        pdf_bytes = generator.generate_report(report_data)

        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'  # PDF magic number

    def test_generate_report_with_seo_metrics(self):
        """Test generating report with SEO metrics."""
        generator = ReportGenerator()

        report_data = ReportData(
            project_id="proj-456",
            project_name="SEO Campaign",
            client_name="Acme Corp",
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_tasks=15,
            completed_tasks=10,
            in_progress_tasks=3,
            blocked_tasks=0,
            estimated_hours=60.0,
            actual_hours=55.0,
            remaining_hours=5.0,
            milestones=[],
            tasks_by_status={"Completed": 10, "In Progress": 3, "Todo": 2},
            tasks_by_assignee={"seo-magister": 15},
            seo_metrics={
                "organic_traffic": 15000,
                "keyword_rankings": {"top_10": 25, "top_20": 45},
                "backlinks": 150,
            },
        )

        pdf_bytes = generator.generate_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_generate_report_with_all_metrics(self):
        """Test generating report with all metric types."""
        generator = ReportGenerator()

        report_data = ReportData(
            project_id="proj-789",
            project_name="Full Marketing Campaign",
            client_name="Big Client",
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_tasks=50,
            completed_tasks=30,
            in_progress_tasks=15,
            blocked_tasks=2,
            estimated_hours=200.0,
            actual_hours=150.0,
            remaining_hours=50.0,
            milestones=[
                {"name": "SEO Phase", "status": "Completed", "progress": 100, "due_date": "2026-05-01"},
                {"name": "Content Phase", "status": "In Progress", "progress": 75, "due_date": "2026-05-15"},
                {"name": "Ads Phase", "status": "Todo", "progress": 0, "due_date": "2026-05-30"},
            ],
            tasks_by_status={"Completed": 30, "In Progress": 15, "Blocked": 2, "Todo": 3},
            tasks_by_assignee={
                "seo-magister": 20,
                "content-magister": 15,
                "ads-magister": 15,
            },
            seo_metrics={"organic_traffic": 20000},
            content_metrics={"articles_published": 12},
            ads_metrics={"impressions": 50000, "clicks": 1500},
        )

        pdf_bytes = generator.generate_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_save_report_to_file(self):
        """Test saving generated report to file."""
        generator = ReportGenerator()

        report_data = ReportData(
            project_id="proj-save",
            project_name="Test Save",
            client_name="Test Client",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            total_tasks=10,
            completed_tasks=5,
            in_progress_tasks=3,
            blocked_tasks=1,
            estimated_hours=40.0,
            actual_hours=20.0,
            remaining_hours=20.0,
            milestones=[],
            tasks_by_status={"Completed": 5, "In Progress": 3, "Blocked": 1, "Todo": 1},
            tasks_by_assignee={"test-agent": 10},
        )

        pdf_bytes = generator.generate_report(report_data)

        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
            f.write(pdf_bytes)
            temp_path = f.name

        # Verify file exists and has content
        assert Path(temp_path).exists()
        assert Path(temp_path).stat().st_size > 0

        # Cleanup
        Path(temp_path).unlink()

    def test_report_with_zero_tasks(self):
        """Test generating report with zero tasks."""
        generator = ReportGenerator()

        report_data = ReportData(
            project_id="proj-empty",
            project_name="Empty Project",
            client_name="Test Client",
            period_start=date.today(),
            period_end=date.today(),
            total_tasks=0,
            completed_tasks=0,
            in_progress_tasks=0,
            blocked_tasks=0,
            estimated_hours=0.0,
            actual_hours=0.0,
            remaining_hours=0.0,
            milestones=[],
            tasks_by_status={},
            tasks_by_assignee={},
        )

        pdf_bytes = generator.generate_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_report_with_custom_brand_color(self):
        """Test report generation with custom brand color."""
        generator = ReportGenerator(brand_color="#FF5733")

        report_data = ReportData(
            project_id="proj-color",
            project_name="Custom Color Project",
            client_name="Test Client",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            total_tasks=10,
            completed_tasks=5,
            in_progress_tasks=3,
            blocked_tasks=1,
            estimated_hours=40.0,
            actual_hours=20.0,
            remaining_hours=20.0,
            milestones=[],
            tasks_by_status={"Completed": 5, "In Progress": 3, "Blocked": 1, "Todo": 1},
            tasks_by_assignee={"test-agent": 10},
        )

        pdf_bytes = generator.generate_report(report_data)

        assert pdf_bytes is not None
        assert generator.brand_color == "#FF5733"

    def test_report_with_many_milestones(self):
        """Test report with many milestones."""
        generator = ReportGenerator()

        milestones = [
            {
                "name": f"Milestone {i}",
                "status": "Completed" if i < 5 else "In Progress",
                "progress": 100 if i < 5 else 50,
                "due_date": f"2026-05-{i+1:02d}",
            }
            for i in range(10)
        ]

        report_data = ReportData(
            project_id="proj-many-milestones",
            project_name="Large Project",
            client_name="Big Client",
            period_start=date.today() - timedelta(days=30),
            period_end=date.today(),
            total_tasks=100,
            completed_tasks=50,
            in_progress_tasks=30,
            blocked_tasks=5,
            estimated_hours=400.0,
            actual_hours=200.0,
            remaining_hours=200.0,
            milestones=milestones,
            tasks_by_status={"Completed": 50, "In Progress": 30, "Blocked": 5, "Todo": 15},
            tasks_by_assignee={"agent-1": 50, "agent-2": 50},
        )

        pdf_bytes = generator.generate_report(report_data)

        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0

    def test_progress_chart_creation(self):
        """Test progress chart is created correctly."""
        generator = ReportGenerator()

        report_data = ReportData(
            project_id="proj-chart",
            project_name="Chart Test",
            client_name="Test Client",
            period_start=date.today() - timedelta(days=7),
            period_end=date.today(),
            total_tasks=20,
            completed_tasks=10,
            in_progress_tasks=5,
            blocked_tasks=2,
            estimated_hours=80.0,
            actual_hours=40.0,
            remaining_hours=40.0,
            milestones=[],
            tasks_by_status={"Completed": 10, "In Progress": 5, "Blocked": 2, "Todo": 3},
            tasks_by_assignee={"test-agent": 20},
        )

        # Generate chart
        chart_path = generator._create_progress_chart(report_data)

        # Verify chart was created
        if chart_path:
            assert Path(chart_path).exists()
            assert Path(chart_path).stat().st_size > 0
            # Cleanup
            Path(chart_path).unlink()
