"""
Business Report Generator

Transforms technical CI analysis into business-oriented reports (PDF + HTML).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import html


class BusinessReportGenerator:
    """Generate business-oriented CI reports in PDF and HTML formats"""

    def __init__(self, deep_analysis: Dict[str, Any]):
        """
        Initialize report generator with deep analysis data

        Args:
            deep_analysis: Output from CIDeepAnalyzer
        """
        self.analysis = deep_analysis
        self.competitor_name = deep_analysis.get("name", "Unknown")
        self.competitor_url = deep_analysis.get("url", "")
        self.analysis_date = deep_analysis.get("analysis_date", datetime.now().isoformat())

    def generate_html(self, output_path: str) -> str:
        """
        Generate HTML report

        Args:
            output_path: Path to save HTML file

        Returns:
            Path to generated HTML file
        """
        # Map technical data to business insights
        business_data = self._map_technical_to_business()

        # Generate HTML content
        html_content = self._generate_html_content(business_data)

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(html_content, encoding='utf-8')

        return str(output_file)

    def generate_pdf(self, output_path: str) -> str:
        """
        Generate PDF report using WeasyPrint

        Args:
            output_path: Path to save PDF file

        Returns:
            Path to generated PDF file
        """
        try:
            from weasyprint import HTML, CSS
        except ImportError:
            raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")

        # Generate HTML content first
        business_data = self._map_technical_to_business()
        html_content = self._generate_html_content(business_data)

        # Convert to PDF
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        HTML(string=html_content).write_pdf(
            str(output_file),
            stylesheets=[CSS(string=self._get_pdf_styles())]
        )

        return str(output_file)

    def _map_technical_to_business(self) -> Dict[str, Any]:
        """
        Map technical metrics to business insights

        Returns:
            Business-oriented data structure
        """
        # Aggregate data from all analyzed pages
        pages = self.analysis.get("pages_analyzed_data", [])

        # Technology Stack Summary
        tech_stack = self._summarize_tech_stack(pages)

        # Marketing Maturity Score
        marketing_score = self._score_marketing_tools(pages)

        # Competitive Positioning
        positioning = self._identify_strengths_weaknesses(pages)

        # Opportunities
        opportunities = self._find_opportunities(pages)

        return {
            "competitor_name": self.competitor_name,
            "competitor_url": self.competitor_url,
            "analysis_date": self.analysis_date,
            "overall_score": self._calculate_overall_score(tech_stack, marketing_score),
            "tech_stack": tech_stack,
            "marketing_maturity": marketing_score,
            "positioning": positioning,
            "opportunities": opportunities
        }

    def _summarize_tech_stack(self, pages: List[Dict]) -> Dict[str, Any]:
        """Summarize technology stack from analyzed pages"""
        if not pages:
            return {}

        # Take first page as representative (homepage usually)
        page = pages[0] if pages else {}

        return {
            "cms": page.get("cms", {}),
            "analytics": page.get("analytics", {}),
            "call_tracking": page.get("call_tracking", {}),
            "live_chat": page.get("live_chat", {}),
            "messengers": page.get("messengers", {}),
            "booking_systems": page.get("booking_systems", {}),
            "payment_systems": page.get("payment_systems", {}),
            "cdn": page.get("cdn", {}),
            "hosting": page.get("hosting", {}),
            "ab_testing": page.get("ab_testing", {})
        }

    def _score_marketing_tools(self, pages: List[Dict]) -> Dict[str, Any]:
        """Score marketing tool maturity"""
        if not pages:
            return {"score": 0, "level": "Начальный"}

        page = pages[0] if pages else {}

        # Count detected marketing tools
        tools_count = 0
        tools_list = []

        # Check each marketing tool
        if page.get("retargeting", {}).get("count", 0) > 0:
            tools_count += 1
            tools_list.append("Ретаргетинг")

        if page.get("email_marketing", {}).get("detected"):
            tools_count += 1
            tools_list.append("Email-маркетинг")

        if page.get("crm", {}).get("detected"):
            tools_count += 1
            tools_list.append("CRM")

        if page.get("quiz_lead_magnets", {}).get("detected"):
            tools_count += 1
            tools_list.append("Квизы/лид-магниты")

        if page.get("social_proof", {}).get("count", 0) > 0:
            tools_count += 1
            tools_list.append("Social proof")

        if page.get("geo_targeting", {}).get("detected"):
            tools_count += 1
            tools_list.append("Гео-таргетинг")

        if page.get("promo_mechanics", {}).get("count", 0) > 0:
            tools_count += 1
            tools_list.append("Промо-механики")

        # Calculate score (0-100)
        score = min(100, tools_count * 14)  # 7 tools max, ~14 points each

        # Determine maturity level
        if score >= 70:
            level = "Продвинутый"
        elif score >= 40:
            level = "Средний"
        else:
            level = "Начальный"

        return {
            "score": score,
            "level": level,
            "tools_count": tools_count,
            "tools_list": tools_list
        }

    def _identify_strengths_weaknesses(self, pages: List[Dict]) -> Dict[str, Any]:
        """Identify competitive strengths and weaknesses"""
        if not pages:
            return {"strengths": [], "weaknesses": []}

        page = pages[0] if pages else {}

        strengths = []
        weaknesses = []

        # Check CMS
        cms = page.get("cms", {})
        if cms.get("confidence", 0) > 0.7:
            strengths.append(f"CMS: {cms.get('cms')} - {cms.get('business_context')}")

        # Check Analytics
        analytics = page.get("analytics", {})
        detected_analytics = [k for k, v in analytics.get("analytics", {}).items() if v.get("detected")]
        if len(detected_analytics) >= 2:
            strengths.append(f"Аналитика: {len(detected_analytics)} инструментов - data-driven подход")
        elif len(detected_analytics) == 0:
            weaknesses.append("Нет аналитики - работают вслепую")

        # Check Call Tracking
        if not page.get("call_tracking", {}).get("detected"):
            weaknesses.append("Нет call tracking - теряют 30% атрибуции лидов")

        # Check Live Chat
        if not page.get("live_chat", {}).get("detected"):
            weaknesses.append("Нет онлайн-чата - упускают горячих лидов")

        # Check Booking
        if not page.get("booking_systems", {}).get("detected"):
            weaknesses.append("Нет онлайн-записи - клиенты уходят к конкурентам")

        # Check Retargeting
        if page.get("retargeting", {}).get("count", 0) == 0:
            weaknesses.append("Нет ретаргетинга - теряют 70% посетителей")

        # Check CRM
        if not page.get("crm", {}).get("detected"):
            weaknesses.append("Нет CRM - теряют лиды и не контролируют воронку")

        return {
            "strengths": strengths[:3],  # Top 3
            "weaknesses": weaknesses[:3]  # Top 3
        }

    def _find_opportunities(self, pages: List[Dict]) -> List[str]:
        """Find opportunities to exploit competitor weaknesses"""
        if not pages:
            return []

        positioning = self._identify_strengths_weaknesses(pages)
        weaknesses = positioning.get("weaknesses", [])

        opportunities = []
        for weakness in weaknesses:
            if "аналитика" in weakness.lower():
                opportunities.append("Внедрить полный стек аналитики - получить преимущество в data-driven решениях")
            elif "call tracking" in weakness.lower():
                opportunities.append("Настроить call tracking - отслеживать источники звонков и ROI")
            elif "чат" in weakness.lower():
                opportunities.append("Добавить онлайн-чат - захватывать горячих лидов в реальном времени")
            elif "запись" in weakness.lower():
                opportunities.append("Внедрить онлайн-запись - упростить конверсию посетителей в клиентов")
            elif "ретаргетинг" in weakness.lower():
                opportunities.append("Запустить ретаргетинг - вернуть 70% ушедших посетителей")
            elif "crm" in weakness.lower():
                opportunities.append("Внедрить CRM - систематизировать работу с лидами и увеличить конверсию")

        return opportunities[:3]  # Top 3

    def _calculate_overall_score(self, tech_stack: Dict, marketing_score: Dict) -> int:
        """Calculate overall competitor score (0-100)"""
        # Tech stack score (50 points max)
        tech_score = 0
        tech_tools = [
            tech_stack.get("cms", {}).get("detected"),
            tech_stack.get("analytics", {}).get("analytics", {}).get("google_analytics", {}).get("detected"),
            tech_stack.get("call_tracking", {}).get("detected"),
            tech_stack.get("live_chat", {}).get("detected"),
            tech_stack.get("booking_systems", {}).get("detected"),
        ]
        tech_score = sum(1 for t in tech_tools if t) * 10  # 10 points per tool

        # Marketing score (50 points max)
        marketing = marketing_score.get("score", 0) // 2  # Scale to 50

        return min(100, tech_score + marketing)

    def _generate_html_content(self, business_data: Dict) -> str:
        """Generate HTML content for report"""
        # Escape all user data
        name = html.escape(business_data["competitor_name"])
        url = html.escape(business_data["competitor_url"])
        date = html.escape(business_data["analysis_date"][:10])

        overall_score = business_data["overall_score"]
        marketing = business_data["marketing_maturity"]

        strengths_html = "".join(f"<li>{html.escape(s)}</li>" for s in business_data["positioning"]["strengths"])
        weaknesses_html = "".join(f"<li>{html.escape(w)}</li>" for w in business_data["positioning"]["weaknesses"])
        opportunities_html = "".join(f"<li>{html.escape(o)}</li>" for o in business_data["opportunities"])

        html_template = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Конкурентный анализ: {name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .score {{ font-size: 48px; font-weight: bold; color: #3498db; }}
        .metric {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
        .strengths {{ color: #27ae60; }}
        .weaknesses {{ color: #e74c3c; }}
        .opportunities {{ color: #f39c12; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Конкурентный анализ</h1>
        <p><strong>Конкурент:</strong> {name}</p>
        <p><strong>URL:</strong> <a href="{url}" style="color: white;">{url}</a></p>
        <p><strong>Дата анализа:</strong> {date}</p>
    </div>

    <div class="metric">
        <h2>Общая оценка</h2>
        <div class="score">{overall_score}/100</div>
    </div>

    <div class="metric">
        <h2>Маркетинговая зрелость</h2>
        <p><strong>Уровень:</strong> {html.escape(marketing['level'])}</p>
        <p><strong>Оценка:</strong> {marketing['score']}/100</p>
        <p><strong>Инструментов:</strong> {marketing['tools_count']}/7</p>
    </div>

    <h2 class="strengths">✅ Сильные стороны</h2>
    <ul>{strengths_html if strengths_html else '<li>Не обнаружено</li>'}</ul>

    <h2 class="weaknesses">⚠️ Слабые стороны</h2>
    <ul>{weaknesses_html if weaknesses_html else '<li>Не обнаружено</li>'}</ul>

    <h2 class="opportunities">💡 Возможности для вас</h2>
    <ul>{opportunities_html if opportunities_html else '<li>Нет рекомендаций</li>'}</ul>

    <footer style="margin-top: 50px; padding-top: 20px; border-top: 1px solid #eee; color: #7f8c8d; font-size: 14px;">
        <p>Сгенерировано AIM CI System v1.0 | {date}</p>
    </footer>
</body>
</html>
"""
        return html_template

    def _get_pdf_styles(self) -> str:
        """Get CSS styles for PDF generation"""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }
        body {
            font-family: 'DejaVu Sans', sans-serif;
        }
        """
