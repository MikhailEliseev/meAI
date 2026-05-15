"""Report generator service - creates PDF reports with ReportLab."""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pathlib import Path
from dataclasses import dataclass
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend


@dataclass
class ReportData:
    """Data for report generation."""
    project_id: str
    project_name: str
    client_name: str
    period_start: date
    period_end: date

    # Progress metrics
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    blocked_tasks: int

    # Time metrics
    estimated_hours: float
    actual_hours: float
    remaining_hours: float

    # Milestones
    milestones: List[Dict[str, Any]]

    # Tasks breakdown
    tasks_by_status: Dict[str, int]
    tasks_by_assignee: Dict[str, int]

    # Optional metrics
    seo_metrics: Optional[Dict[str, Any]] = None
    content_metrics: Optional[Dict[str, Any]] = None
    ads_metrics: Optional[Dict[str, Any]] = None


class ReportGenerator:
    """Generates PDF reports for client projects.

    Creates professional PDF reports with:
    - Project overview and progress
    - Task completion metrics
    - Milestone tracking
    - Charts and visualizations
    - Branded design

    Example:
        generator = ReportGenerator(
            logo_path="assets/logo.png",
            brand_color="#1E40AF"
        )

        report_data = ReportData(
            project_id="proj-123",
            project_name="SEO Audit",
            client_name="Acme Corp",
            ...
        )

        pdf_bytes = generator.generate_report(report_data)

        # Save to file
        with open("report.pdf", "wb") as f:
            f.write(pdf_bytes)
    """

    def __init__(
        self,
        logo_path: Optional[str] = None,
        brand_color: str = "#1E40AF",
        page_size: tuple = A4,
    ):
        """Initialize report generator.

        Args:
            logo_path: Path to company logo image
            brand_color: Hex color for branding
            page_size: Page size (default: A4)
        """
        self.logo_path = logo_path
        self.brand_color = brand_color
        self.page_size = page_size

        # Setup styles
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self) -> None:
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(self.brand_color),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor(self.brand_color),
            spaceBefore=20,
            spaceAfter=12,
            borderWidth=0,
            borderColor=colors.HexColor(self.brand_color),
            borderPadding=5,
        ))

        # Metric style
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=6,
        ))

    def generate_report(self, data: ReportData) -> bytes:
        """Generate PDF report from data.

        Args:
            data: Report data

        Returns:
            PDF file as bytes
        """
        # Create PDF in memory
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Build content
        story = []

        # Header with logo
        story.extend(self._build_header(data))

        # Executive summary
        story.extend(self._build_executive_summary(data))

        # Progress overview
        story.extend(self._build_progress_section(data))

        # Milestones
        story.extend(self._build_milestones_section(data))

        # Tasks breakdown
        story.extend(self._build_tasks_section(data))

        # Domain-specific metrics (if available)
        if data.seo_metrics:
            story.extend(self._build_seo_section(data.seo_metrics))

        if data.content_metrics:
            story.extend(self._build_content_section(data.content_metrics))

        if data.ads_metrics:
            story.extend(self._build_ads_section(data.ads_metrics))

        # Footer
        story.extend(self._build_footer(data))

        # Build PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes

    def _build_header(self, data: ReportData) -> List:
        """Build report header with logo and title."""
        elements = []

        # Logo (if provided)
        if self.logo_path and Path(self.logo_path).exists():
            logo = Image(self.logo_path, width=2*inch, height=0.8*inch)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.3*inch))

        # Title
        title = Paragraph(
            f"Project Report: {data.project_name}",
            self.styles['CustomTitle']
        )
        elements.append(title)

        # Client and period
        info_text = f"""
        <b>Client:</b> {data.client_name}<br/>
        <b>Period:</b> {data.period_start.strftime('%B %d, %Y')} - {data.period_end.strftime('%B %d, %Y')}<br/>
        <b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %H:%M')}
        """
        info = Paragraph(info_text, self.styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.5*inch))

        return elements

    def _build_executive_summary(self, data: ReportData) -> List:
        """Build executive summary section."""
        elements = []

        # Section header
        header = Paragraph("Executive Summary", self.styles['SectionHeader'])
        elements.append(header)

        # Calculate completion percentage
        completion_pct = (data.completed_tasks / data.total_tasks * 100) if data.total_tasks > 0 else 0

        # Summary text
        summary_text = f"""
        This report covers the period from {data.period_start.strftime('%B %d')} to {data.period_end.strftime('%B %d, %Y')}.
        <br/><br/>
        <b>Overall Progress:</b> {completion_pct:.1f}% complete ({data.completed_tasks} of {data.total_tasks} tasks)<br/>
        <b>Time Tracking:</b> {data.actual_hours:.1f} hours spent of {data.estimated_hours:.1f} estimated<br/>
        <b>Status:</b> {data.in_progress_tasks} tasks in progress, {data.blocked_tasks} blocked
        """
        summary = Paragraph(summary_text, self.styles['Normal'])
        elements.append(summary)
        elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_progress_section(self, data: ReportData) -> List:
        """Build progress overview with chart."""
        elements = []

        # Section header
        header = Paragraph("Progress Overview", self.styles['SectionHeader'])
        elements.append(header)

        # Create progress chart
        chart_path = self._create_progress_chart(data)
        if chart_path:
            chart_img = Image(chart_path, width=5*inch, height=3*inch)
            chart_img.hAlign = 'CENTER'
            elements.append(chart_img)
            elements.append(Spacer(1, 0.2*inch))

        return elements

    def _build_milestones_section(self, data: ReportData) -> List:
        """Build milestones section with table."""
        elements = []

        # Section header
        header = Paragraph("Milestones", self.styles['SectionHeader'])
        elements.append(header)

        # Milestones table
        if data.milestones:
            table_data = [['Milestone', 'Status', 'Progress', 'Due Date']]

            for milestone in data.milestones:
                table_data.append([
                    milestone.get('name', 'N/A'),
                    milestone.get('status', 'N/A'),
                    f"{milestone.get('progress', 0):.0f}%",
                    milestone.get('due_date', 'N/A'),
                ])

            table = Table(table_data, colWidths=[3*inch, 1.2*inch, 1*inch, 1.3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.brand_color)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_tasks_section(self, data: ReportData) -> List:
        """Build tasks breakdown section."""
        elements = []

        # Section header
        header = Paragraph("Tasks Breakdown", self.styles['SectionHeader'])
        elements.append(header)

        # Tasks by status
        if data.tasks_by_status:
            status_text = "<b>By Status:</b><br/>"
            for status, count in data.tasks_by_status.items():
                status_text += f"• {status}: {count}<br/>"

            status_para = Paragraph(status_text, self.styles['Normal'])
            elements.append(status_para)
            elements.append(Spacer(1, 0.2*inch))

        # Tasks by assignee
        if data.tasks_by_assignee:
            assignee_text = "<b>By Assignee:</b><br/>"
            for assignee, count in data.tasks_by_assignee.items():
                assignee_text += f"• {assignee}: {count}<br/>"

            assignee_para = Paragraph(assignee_text, self.styles['Normal'])
            elements.append(assignee_para)
            elements.append(Spacer(1, 0.3*inch))

        return elements

    def _build_seo_section(self, metrics: Dict[str, Any]) -> List:
        """Build SEO metrics section."""
        elements = []

        header = Paragraph("SEO Metrics", self.styles['SectionHeader'])
        elements.append(header)

        # Add SEO-specific metrics here
        # TODO: Implement based on actual SEO metrics structure

        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _build_content_section(self, metrics: Dict[str, Any]) -> List:
        """Build content metrics section."""
        elements = []

        header = Paragraph("Content Metrics", self.styles['SectionHeader'])
        elements.append(header)

        # Add content-specific metrics here
        # TODO: Implement based on actual content metrics structure

        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _build_ads_section(self, metrics: Dict[str, Any]) -> List:
        """Build ads metrics section."""
        elements = []

        header = Paragraph("Advertising Metrics", self.styles['SectionHeader'])
        elements.append(header)

        # Add ads-specific metrics here
        # TODO: Implement based on actual ads metrics structure

        elements.append(Spacer(1, 0.3*inch))
        return elements

    def _build_footer(self, data: ReportData) -> List:
        """Build report footer."""
        elements = []

        elements.append(Spacer(1, 0.5*inch))

        footer_text = """
        <i>This report was automatically generated by AIM Agency Operations System.</i><br/>
        <i>For questions or concerns, please contact your project manager.</i>
        """
        footer = Paragraph(footer_text, self.styles['Normal'])
        elements.append(footer)

        return elements

    def _create_progress_chart(self, data: ReportData) -> Optional[str]:
        """Create progress pie chart.

        Returns:
            Path to saved chart image, or None if failed
        """
        try:
            # Create figure
            fig, ax = plt.subplots(figsize=(6, 4))

            # Data
            labels = ['Completed', 'In Progress', 'Blocked', 'Not Started']
            not_started = data.total_tasks - data.completed_tasks - data.in_progress_tasks - data.blocked_tasks
            sizes = [data.completed_tasks, data.in_progress_tasks, data.blocked_tasks, not_started]
            colors_list = ['#10B981', '#3B82F6', '#EF4444', '#9CA3AF']

            # Create pie chart
            ax.pie(sizes, labels=labels, colors=colors_list, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')

            # Save to temp file
            chart_path = f"/tmp/progress_chart_{data.project_id}.png"
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()

            return chart_path

        except Exception as e:
            print(f"Failed to create progress chart: {e}")
            return None

    def _add_page_number(self, canvas_obj: canvas.Canvas, doc) -> None:
        """Add page number to footer."""
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.saveState()
        canvas_obj.setFont('Helvetica', 9)
        canvas_obj.drawRightString(
            doc.pagesize[0] - 72,
            30,
            text
        )
        canvas_obj.restoreState()
