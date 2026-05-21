"""Analytics Report Generator

Generates analytics reports in CSV, JSON, and PDF formats.

Part of: Phase 11 Sprint 2 - Task 2.5
"""

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from aim.schemas.analytics import (
    ConversionFunnel,
    EmailMetrics,
    LeadMetrics,
    RealTimeStats,
)


class ReportGenerator:
    """Generate analytics reports in various formats."""

    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save generated reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_csv_report(
        self,
        lead_metrics: LeadMetrics,
        email_metrics: EmailMetrics,
        funnel: ConversionFunnel,
    ) -> str:
        """
        Generate CSV report with all metrics.

        Args:
            lead_metrics: Lead acquisition metrics
            email_metrics: Email campaign metrics
            funnel: Conversion funnel metrics

        Returns:
            Path to generated CSV file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.csv"
        filepath = self.output_dir / filename

        with open(filepath, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Header
            writer.writerow(["Analytics Report"])
            writer.writerow(
                [
                    f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                ]
            )
            writer.writerow(
                [
                    f"Period: {lead_metrics.start_date.strftime('%Y-%m-%d')} to {lead_metrics.end_date.strftime('%Y-%m-%d')}"
                ]
            )
            writer.writerow([])

            # Lead Metrics
            writer.writerow(["LEAD METRICS"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Leads", lead_metrics.total_leads])
            writer.writerow(["Average Score", f"{lead_metrics.average_score:.2f}"])
            writer.writerow(["Capture Rate", f"{lead_metrics.capture_rate:.2f}"])
            writer.writerow(["Duplicate Rate", f"{lead_metrics.duplicate_rate:.2f}%"])
            writer.writerow([])

            # Leads by Tier
            writer.writerow(["Leads by Tier"])
            writer.writerow(["Tier", "Count"])
            for tier, count in lead_metrics.leads_by_tier.items():
                writer.writerow([tier.capitalize(), count])
            writer.writerow([])

            # Leads by Source
            writer.writerow(["Leads by Source"])
            writer.writerow(["Source", "Count"])
            for source, count in lead_metrics.leads_by_source.items():
                writer.writerow([source.replace("_", " ").title(), count])
            writer.writerow([])

            # Email Metrics
            writer.writerow(["EMAIL METRICS"])
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Sent", email_metrics.total_sent])
            writer.writerow(["Total Delivered", email_metrics.total_delivered])
            writer.writerow(["Total Opened", email_metrics.total_opened])
            writer.writerow(["Total Clicked", email_metrics.total_clicked])
            writer.writerow(["Delivery Rate", f"{email_metrics.delivery_rate:.2f}%"])
            writer.writerow(["Open Rate", f"{email_metrics.open_rate:.2f}%"])
            writer.writerow(["Click Rate", f"{email_metrics.click_rate:.2f}%"])
            writer.writerow(["Bounce Rate", f"{email_metrics.bounce_rate:.2f}%"])
            writer.writerow([])

            # Conversion Funnel
            writer.writerow(["CONVERSION FUNNEL"])
            writer.writerow(["Stage", "Count"])
            writer.writerow(["Leads Captured", funnel.leads_captured])
            writer.writerow(["Leads Scored", funnel.leads_scored])
            writer.writerow(["Tasks Created", funnel.tasks_created])
            writer.writerow(["Workflows Triggered", funnel.workflows_triggered])
            writer.writerow(["Emails Sent", funnel.emails_sent])
            writer.writerow(["Emails Delivered", funnel.emails_delivered])
            writer.writerow(["Emails Opened", funnel.emails_opened])
            writer.writerow(["Emails Clicked", funnel.emails_clicked])
            writer.writerow([])

            # Conversion Rates
            writer.writerow(["Conversion Rates"])
            writer.writerow(["Stage", "Rate"])
            for stage, rate in funnel.conversion_rates.items():
                writer.writerow([stage.replace("_", " ").title(), f"{rate:.2f}%"])

        return str(filepath)

    def generate_json_report(
        self,
        lead_metrics: LeadMetrics,
        email_metrics: EmailMetrics,
        funnel: ConversionFunnel,
        realtime_stats: RealTimeStats,
    ) -> str:
        """
        Generate JSON report with all metrics.

        Args:
            lead_metrics: Lead acquisition metrics
            email_metrics: Email campaign metrics
            funnel: Conversion funnel metrics
            realtime_stats: Real-time statistics

        Returns:
            Path to generated JSON file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"
        filepath = self.output_dir / filename

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period": {
                "start": lead_metrics.start_date.isoformat(),
                "end": lead_metrics.end_date.isoformat(),
            },
            "lead_metrics": lead_metrics.model_dump(),
            "email_metrics": email_metrics.model_dump(),
            "conversion_funnel": funnel.model_dump(),
            "realtime_stats": realtime_stats.model_dump(),
        }

        with open(filepath, "w") as jsonfile:
            json.dump(report, jsonfile, indent=2, default=str)

        return str(filepath)

    def generate_pdf_report(
        self,
        lead_metrics: LeadMetrics,
        email_metrics: EmailMetrics,
        funnel: ConversionFunnel,
        include_charts: bool = False,
    ) -> str:
        """
        Generate PDF report with formatted tables and optional charts.

        Args:
            lead_metrics: Lead acquisition metrics
            email_metrics: Email campaign metrics
            funnel: Conversion funnel metrics
            include_charts: Include charts in report (not implemented yet)

        Returns:
            Path to generated PDF file
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.pdf"
        filepath = self.output_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for PDF elements
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#333333"),
            spaceAfter=12,
        )

        # Title
        story.append(Paragraph("Analytics Report", title_style))
        story.append(
            Paragraph(
                f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"Period: {lead_metrics.start_date.strftime('%Y-%m-%d')} to {lead_metrics.end_date.strftime('%Y-%m-%d')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        summary_data = [
            ["Metric", "Value"],
            ["Total Leads", str(lead_metrics.total_leads)],
            ["Average Lead Score", f"{lead_metrics.average_score:.2f}"],
            ["Emails Sent", str(email_metrics.total_sent)],
            ["Email Open Rate", f"{email_metrics.open_rate:.2f}%"],
            ["Email Click Rate", f"{email_metrics.click_rate:.2f}%"],
        ]
        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # Lead Metrics
        story.append(Paragraph("Lead Acquisition", heading_style))
        lead_data = [
            ["Metric", "Value"],
            ["Total Leads", str(lead_metrics.total_leads)],
            ["Average Score", f"{lead_metrics.average_score:.2f}"],
            ["Capture Rate (per day)", f"{lead_metrics.capture_rate:.2f}"],
            ["Duplicate Rate", f"{lead_metrics.duplicate_rate:.2f}%"],
        ]
        lead_table = Table(lead_data, colWidths=[3 * inch, 2 * inch])
        lead_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(lead_table)
        story.append(Spacer(1, 0.2 * inch))

        # Leads by Tier
        tier_data = [["Tier", "Count"]]
        for tier, count in lead_metrics.leads_by_tier.items():
            tier_data.append([tier.capitalize(), str(count)])
        tier_table = Table(tier_data, colWidths=[3 * inch, 2 * inch])
        tier_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(tier_table)
        story.append(Spacer(1, 0.3 * inch))

        # Email Campaign Performance
        story.append(Paragraph("Email Campaign Performance", heading_style))
        email_data = [
            ["Metric", "Value"],
            ["Total Sent", str(email_metrics.total_sent)],
            ["Total Delivered", str(email_metrics.total_delivered)],
            ["Total Opened", str(email_metrics.total_opened)],
            ["Total Clicked", str(email_metrics.total_clicked)],
            ["Delivery Rate", f"{email_metrics.delivery_rate:.2f}%"],
            ["Open Rate", f"{email_metrics.open_rate:.2f}%"],
            ["Click Rate", f"{email_metrics.click_rate:.2f}%"],
            ["Bounce Rate", f"{email_metrics.bounce_rate:.2f}%"],
        ]
        email_table = Table(email_data, colWidths=[3 * inch, 2 * inch])
        email_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(email_table)
        story.append(Spacer(1, 0.3 * inch))

        # Conversion Funnel
        story.append(Paragraph("Conversion Funnel", heading_style))
        funnel_data = [
            ["Stage", "Count", "Conversion Rate"],
            ["Leads Captured", str(funnel.leads_captured), "-"],
            [
                "Leads Scored",
                str(funnel.leads_scored),
                f"{funnel.conversion_rates.get('capture_to_score', 0):.2f}%",
            ],
            [
                "Tasks Created",
                str(funnel.tasks_created),
                f"{funnel.conversion_rates.get('score_to_task', 0):.2f}%",
            ],
            [
                "Workflows Triggered",
                str(funnel.workflows_triggered),
                f"{funnel.conversion_rates.get('task_to_workflow', 0):.2f}%",
            ],
            [
                "Emails Sent",
                str(funnel.emails_sent),
                f"{funnel.conversion_rates.get('workflow_to_sent', 0):.2f}%",
            ],
            [
                "Emails Delivered",
                str(funnel.emails_delivered),
                f"{funnel.conversion_rates.get('sent_to_delivered', 0):.2f}%",
            ],
            [
                "Emails Opened",
                str(funnel.emails_opened),
                f"{funnel.conversion_rates.get('delivered_to_opened', 0):.2f}%",
            ],
            [
                "Emails Clicked",
                str(funnel.emails_clicked),
                f"{funnel.conversion_rates.get('opened_to_clicked', 0):.2f}%",
            ],
        ]
        funnel_table = Table(funnel_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
        funnel_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )
        story.append(funnel_table)
        story.append(Spacer(1, 0.3 * inch))

        # Recommendations
        story.append(Paragraph("Recommendations", heading_style))
        recommendations = self._generate_recommendations(
            lead_metrics, email_metrics, funnel
        )
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", styles["Normal"]))
            story.append(Spacer(1, 0.1 * inch))

        # Build PDF
        doc.build(story)

        return str(filepath)

    def _generate_recommendations(
        self,
        lead_metrics: LeadMetrics,
        email_metrics: EmailMetrics,
        funnel: ConversionFunnel,
    ) -> list[str]:
        """
        Generate recommendations based on metrics.

        Args:
            lead_metrics: Lead acquisition metrics
            email_metrics: Email campaign metrics
            funnel: Conversion funnel metrics

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Lead capture recommendations
        if lead_metrics.capture_rate < 5:
            recommendations.append(
                "Low lead capture rate detected. Consider increasing marketing spend or optimizing landing pages."
            )

        if lead_metrics.duplicate_rate > 10:
            recommendations.append(
                "High duplicate rate detected. Review lead capture forms and implement better deduplication."
            )

        # Email performance recommendations
        if email_metrics.open_rate < 20:
            recommendations.append(
                "Email open rate is below industry average (20%). Test different subject lines and send times."
            )

        if email_metrics.click_rate < 10:
            recommendations.append(
                "Email click rate is below target (10%). Improve email content and call-to-action clarity."
            )

        if email_metrics.bounce_rate > 5:
            recommendations.append(
                "High bounce rate detected. Clean email list and verify email addresses at capture."
            )

        # Conversion funnel recommendations
        capture_to_score = funnel.conversion_rates.get("capture_to_score", 0)
        if capture_to_score < 90:
            recommendations.append(
                "Lead scoring conversion is low. Review scoring criteria and ensure all leads are processed."
            )

        score_to_task = funnel.conversion_rates.get("score_to_task", 0)
        if score_to_task < 30:
            recommendations.append(
                "Low task creation rate. Consider lowering threshold for Linear task creation or improving lead quality."
            )

        delivered_to_opened = funnel.conversion_rates.get("delivered_to_opened", 0)
        if delivered_to_opened < 25:
            recommendations.append(
                "Low email open rate in funnel. Segment audience better and personalize subject lines."
            )

        if not recommendations:
            recommendations.append(
                "All metrics are within acceptable ranges. Continue monitoring and optimizing campaigns."
            )

        return recommendations
