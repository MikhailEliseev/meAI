"""PDF-конвертация HTML→PDF через WeasyPrint (Phase 12).

WeasyPrint: Python-библиотека для HTML→PDF через Cairo/Pango.
Поддерживает @media print, CSS page breaks, footer с нумерацией страниц.
Не исполняет JS (theme toggle не работает в PDF, но для печати это OK).
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def html_to_pdf(html: str) -> bytes:
    """Конвертирует HTML в PDF через WeasyPrint.
    
    Args:
        html: HTML-строка отчёта (из MySQL wp_posts.post_content)
    
    Returns:
        PDF в виде bytes
    
    Raises:
        Exception: При ошибке конвертации (WeasyPrint, CSS, шрифты)
    """
    from weasyprint import HTML, CSS
    
    # Загрузить print CSS (если есть отдельный файл)
    print_css_path = Path(__file__).parent / "print.css"
    stylesheets = []
    if print_css_path.exists():
        logger.info("Loading print.css from %s", print_css_path)
        stylesheets.append(CSS(filename=str(print_css_path)))
    
    # HTML→PDF
    try:
        html_doc = HTML(string=html)
        pdf_bytes = html_doc.write_pdf(stylesheets=stylesheets)
        logger.info("PDF generated: %d bytes", len(pdf_bytes))
        return pdf_bytes
    except Exception as e:
        logger.error("WeasyPrint PDF generation failed: %s", e)
        raise
