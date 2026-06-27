"""
generate_html_report.py — Canonical Template Approach

Per D-14: LLM generates content (text, data), Python assembles HTML.
Per D-15: Uses report-template.html with Jinja2 placeholders.

Fixes "полный крах вёрстки" by separating structure from content.

This replaces the previous 3370-line monolithic HTML generator with a clean
template-based approach. The canonical template (report-template.html) contains
all design-showcase CSS and structure. This script only builds section content
from orchestrator data.
"""

import json
import logging
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

# Templates directory relative to this script
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def generate_report_html(
    clinic_name: str,
    sections: dict,
    output_path: Path
) -> bool:
    """Generate HTML report using canonical template.

    Args:
        clinic_name: Clinic name for title
        sections: Dict with keys matching template placeholders:
            {
                "clinic_overview_html": "<p>...</p>",
                "competitors_html": "<div>...</div>",
                "experts_html": "...",
                "content_analysis_html": "...",
                "whitefields_html": "...",
                "seo_html": "...",
                "ads_html": "...",
                "tech_audit_html": "...",
                "strategy_html": "...",
                "offer_html": "..."
            }
        output_path: Where to save the report

    Returns:
        True if successful, False otherwise
    """
    try:
        # Load template
        if not TEMPLATES_DIR.exists():
            logger.error("Templates directory not found: %s", TEMPLATES_DIR)
            return False

        env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
        template = env.get_template("report-template.html")

        # Ensure all required sections are present
        required_sections = [
            "clinic_overview_html",
            "competitors_html",
            "experts_html",
            "content_analysis_html",
            "whitefields_html",
            "seo_html",
            "ads_html",
            "tech_audit_html",
            "strategy_html",
            "offer_html"
        ]

        # Fill in missing sections with placeholder
        for section in required_sections:
            if section not in sections or sections[section] is None:
                sections[section] = "<p>Данные отсутствуют</p>"

        # Render with sections
        html = template.render(
            clinic_name=clinic_name,
            **sections
        )

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        logger.info("Report generated: %s (%d bytes)", output_path, len(html))
        return True

    except Exception as e:
        logger.exception("Failed to generate report")
        return False


def sections_from_orchestrator_output(data: dict) -> dict:
    """Convert orchestrator output to template sections.

    Args:
        data: Output from 3-pass orchestrator or PipelineEngine

    Returns:
        Dict with HTML sections ready for template
    """
    sections = {}

    # Map orchestrator keys to template placeholders
    # Phase 4+5 data structures will populate these
    sections["clinic_overview_html"] = _build_clinic_overview(data)
    sections["competitors_html"] = _build_competitors(data)
    sections["experts_html"] = _build_experts(data)
    sections["content_analysis_html"] = _build_content_analysis(data)
    sections["whitefields_html"] = _build_whitefields(data)
    sections["seo_html"] = _build_seo(data)
    sections["ads_html"] = _build_ads(data)
    sections["tech_audit_html"] = _build_tech_audit(data)
    sections["strategy_html"] = _build_strategy(data)
    sections["offer_html"] = _build_offer(data)

    return sections


def _build_clinic_overview(data: dict) -> str:
    """Build clinic overview HTML from data.

    Expected data structure:
        - financials: revenue, revenue_trend, year_founded
        - clinic_metrics: doctors_count, licenses, okved_codes
    """
    financials = data.get("financials", {})
    metrics = data.get("clinic_metrics", {})

    if not financials and not metrics:
        return "<p>Финансовые данные и метрики клиники недоступны.</p>"

    html_parts = []

    # Revenue card
    revenue = financials.get("revenue")
    trend = financials.get("revenue_trend", "—")
    if revenue:
        revenue_fmt = _format_revenue(revenue)
        trend_class = _trend_to_class(trend)
        html_parts.append(f"""
        <div class="card-glass">
            <h3>Выручка</h3>
            <p style="font-size: 32px; font-weight: 600; color: var(--accent); margin: 12px 0;">
                {revenue_fmt}
            </p>
            <span class="metric-tag metric-tag-{trend_class}">
                <span class="metric-tag-dot"></span>
                Тренд: {trend}
            </span>
        </div>
        """)

    # Basic metrics
    if metrics:
        html_parts.append("<div class='card-glass'><h3>Основные показатели</h3><ul>")
        if metrics.get("year_founded"):
            html_parts.append(f"<li>Год основания: {metrics['year_founded']}</li>")
        if metrics.get("doctors_count"):
            html_parts.append(f"<li>Количество врачей: {metrics['doctors_count']}</li>")
        if metrics.get("licenses"):
            html_parts.append(f"<li>Лицензии: {metrics['licenses']}</li>")
        html_parts.append("</ul></div>")

    return "".join(html_parts)


def _build_competitors(data: dict) -> str:
    """Build competitors section HTML.

    Expected data: list of competitor dicts with name, revenue, instagram, etc.
    """
    competitors = data.get("competitors", [])

    if not competitors:
        return "<p>Конкуренты не найдены.</p>"

    html_parts = []
    for comp in competitors:
        name = comp.get("name", "Неизвестно")
        revenue = comp.get("revenue")
        instagram = comp.get("instagram_handle", "—")

        revenue_fmt = _format_revenue(revenue) if revenue else "—"

        html_parts.append(f"""
        <div class="card-glass">
            <h3>{_esc(name)}</h3>
            <p>Выручка: <strong>{revenue_fmt}</strong></p>
            <p>Instagram: <strong>{_esc(instagram)}</strong></p>
        </div>
        """)

    return "".join(html_parts)


def _build_experts(data: dict) -> str:
    """Build experts (top doctors) section HTML.

    Expected data: instagram_data with top_doctors list
    """
    instagram = data.get("instagram_data", {})
    doctors = instagram.get("top_doctors", [])

    if not doctors:
        return "<p>Данные о врачах клиники в Instagram недоступны.</p>"

    html_parts = []
    for doc in doctors[:5]:  # Top 5
        name = doc.get("name", "Неизвестно")
        handle = doc.get("handle", "—")
        followers = doc.get("followers", 0)

        html_parts.append(f"""
        <div class="card-glass">
            <h3>{_esc(name)}</h3>
            <p>@{_esc(handle)} • {followers:,} подписчиков</p>
        </div>
        """)

    return "".join(html_parts)


def _build_content_analysis(data: dict) -> str:
    """Build content analysis section HTML."""
    content = data.get("content_analysis", {})

    if not content:
        return "<p>Контент-анализ недоступен.</p>"

    html_parts = ["<div class='card-glass'>"]
    html_parts.append("<h3>Анализ контента</h3>")
    html_parts.append(f"<p>{content.get('summary', 'Данные отсутствуют')}</p>")
    html_parts.append("</div>")

    return "".join(html_parts)


def _build_whitefields(data: dict) -> str:
    """Build whitefields (gaps) section HTML."""
    whitefields = data.get("whitefields", [])

    if not whitefields:
        return "<p>Белые поля не обнаружены.</p>"

    html_parts = ["<div class='card-glass'><h3>Обнаруженные пробелы</h3><ul>"]
    for field in whitefields:
        html_parts.append(f"<li>{_esc(field)}</li>")
    html_parts.append("</ul></div>")

    return "".join(html_parts)


def _build_seo(data: dict) -> str:
    """Build SEO section HTML."""
    seo = data.get("seo_audit", {})

    if not seo:
        return "<p>SEO-аудит недоступен.</p>"

    html_parts = []

    # Core metrics
    metrics_card = "<div class='card-glass'><h3>Ключевые метрики</h3><ul>"
    if "lcp" in seo:
        metrics_card += f"<li>LCP: {seo['lcp']} сек</li>"
    if "fid" in seo:
        metrics_card += f"<li>FID: {seo['fid']} мс</li>"
    if "cls" in seo:
        metrics_card += f"<li>CLS: {seo['cls']}</li>"
    metrics_card += "</ul></div>"

    html_parts.append(metrics_card)

    return "".join(html_parts)


def _build_ads(data: dict) -> str:
    """Build advertising section HTML."""
    ads = data.get("ads_report", {})

    if not ads:
        return "<p>Данные о рекламе недоступны.</p>"

    html_parts = ["<div class='card-glass'>"]
    html_parts.append("<h3>Рекламные кампании</h3>")
    html_parts.append(f"<p>{ads.get('summary', 'Данные отсутствуют')}</p>")
    html_parts.append("</div>")

    return "".join(html_parts)


def _build_tech_audit(data: dict) -> str:
    """Build technical audit section HTML."""
    tech = data.get("tech_audit", {})

    if not tech:
        return "<p>Технический аудит недоступен.</p>"

    html_parts = ["<div class='card-glass'>"]
    html_parts.append("<h3>Технические находки</h3>")
    html_parts.append(f"<p>{tech.get('summary', 'Данные отсутствуют')}</p>")
    html_parts.append("</div>")

    return "".join(html_parts)


def _build_strategy(data: dict) -> str:
    """Build strategy recommendations section HTML."""
    strategy = data.get("strategy", {})

    if not strategy:
        return "<p>Стратегические рекомендации будут добавлены в следующих версиях.</p>"

    html_parts = ["<div class='card-glass'>"]
    html_parts.append("<h3>Рекомендации</h3>")

    recommendations = strategy.get("recommendations", [])
    if recommendations:
        html_parts.append("<ol>")
        for rec in recommendations:
            html_parts.append(f"<li>{_esc(rec)}</li>")
        html_parts.append("</ol>")
    else:
        html_parts.append("<p>Рекомендации отсутствуют</p>")

    html_parts.append("</div>")

    return "".join(html_parts)


def _build_offer(data: dict) -> str:
    """Build AIM offer section HTML."""
    offer = data.get("offer", {})

    # Default offer if not in data
    if not offer:
        return """
        <div class="card-glass">
            <h3>Персональное предложение</h3>
            <p>На основе проведённого анализа команда AIM готова предложить вам решения для устранения выявленных пробелов и усиления конкурентных позиций.</p>
            <p style="margin-top: 16px;">
                <a href="https://iamaim.ru/pricing" class="btn-primary" style="display: inline-block; margin-top: 12px;">
                    Обсудить с менеджером
                </a>
            </p>
        </div>
        """

    html_parts = ["<div class='card-glass'>"]
    html_parts.append(f"<h3>{offer.get('title', 'Наше предложение')}</h3>")
    html_parts.append(f"<p>{offer.get('description', 'Свяжитесь с нами для обсуждения деталей.')}</p>")
    html_parts.append("</div>")

    return "".join(html_parts)


# === Helper Functions ===

def _esc(text: str) -> str:
    """Escape HTML special characters."""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def _format_revenue(val) -> str:
    """Format revenue as human-readable: 4.3 млрд ₽, 742 млн ₽, 12.5 млн ₽."""
    if val is None:
        return "—"
    if not isinstance(val, (int, float)):
        return str(val)
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f} млрд ₽"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.0f} млн ₽"
    if val >= 1_000:
        return f"{val / 1_000:.0f} тыс ₽"
    return f"{int(val):,} ₽".replace(",", " ")


def _trend_to_class(trend: str) -> str:
    """Convert trend string to metric-tag class."""
    if not trend:
        return "gray"
    t = trend.lower()
    if "рост" in t or "↑" in t:
        return "green"
    if "падение" in t or "↓" in t:
        return "red"
    if "стабильн" in t or "→" in t:
        return "blue"
    return "gray"


# === Test Harness ===

if __name__ == "__main__":
    # Test render with stub data
    test_sections = {
        "clinic_overview_html": "<div class='card-glass'><h3>Тестовая клиника</h3><p>Выручка: 150 млн ₽</p></div>",
        "competitors_html": "<div class='card-glass'><h3>Конкурент 1</h3><p>Выручка: 200 млн ₽</p></div>",
        "experts_html": "<p>ТОП-5 врачей будут добавлены после интеграции Instagram</p>",
        "content_analysis_html": "<p>Контент-анализ в разработке</p>",
        "whitefields_html": "<p>Пробелы не обнаружены</p>",
        "seo_html": "<p>SEO-аудит в разработке</p>",
        "ads_html": "<p>Рекламные данные в разработке</p>",
        "tech_audit_html": "<p>Технический аудит в разработке</p>",
        "strategy_html": "<p>Стратегия в разработке</p>",
        "offer_html": "<div class='card-glass'><h3>Наше предложение</h3><p>AIM готова помочь</p></div>"
    }

    output = Path("/tmp/test-report.html")
    success = generate_report_html("Тестовая Клиника", test_sections, output)

    if success:
        print(f"✓ Test render: OK")
        print(f"  Output: {output}")
        print(f"  Size: {output.stat().st_size} bytes")
    else:
        print(f"✗ Test render: FAIL")
