"""Unit-тесты для Phase 12: Report Download (PDF через WeasyPrint).

Тест-кейсы:
1. test_download_endpoint_returns_pdf — GET /api/report/{slug}/download → 200, PDF
2. test_download_headers_pdf — проверить Content-Type: application/pdf
3. test_download_not_found — GET с несуществующим slug → 404
4. test_pdf_content_valid — PDF начинается с %PDF-1.
5. test_frontend_button_exists — renderReportCard() содержит кнопку "Скачать PDF"
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Добавим путь к app/ для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_download_endpoint_returns_pdf():
    """GET /api/report/{slug}/download возвращает PDF (200)."""
    mock_html = "<html><body><h1>Test Report</h1></body></html>"
    mock_pdf = b"%PDF-1.4\n%test pdf content"
    
    with patch("app.report_builder.publisher.get_report_html_by_slug", new=AsyncMock(return_value=mock_html)):
        with patch("app.report_builder.pdf_converter.html_to_pdf", return_value=mock_pdf):
            response = client.get("/api/report/testslug/download")
    
    assert response.status_code == 200
    assert response.content == mock_pdf


def test_download_headers_pdf():
    """Проверить Content-Type: application/pdf и Content-Disposition."""
    mock_html = "<html><body>Test</body></html>"
    mock_pdf = b"%PDF-1.4\ntest"
    
    with patch("app.report_builder.publisher.get_report_html_by_slug", new=AsyncMock(return_value=mock_html)):
        with patch("app.report_builder.pdf_converter.html_to_pdf", return_value=mock_pdf):
            response = client.get("/api/report/abc123/download")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert "report-abc123.pdf" in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_not_found():
    """GET с несуществующим slug возвращает 404."""
    with patch("app.report_builder.publisher.get_report_html_by_slug", new=AsyncMock(return_value=None)):
        response = client.get("/api/report/nonexistent/download")
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_pdf_content_valid():
    """PDF начинается с %PDF-1. (валидный PDF magic number)."""
    mock_html = "<html><body>Valid Report</body></html>"
    mock_pdf = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"  # Валидный PDF header
    
    with patch("app.report_builder.publisher.get_report_html_by_slug", new=AsyncMock(return_value=mock_html)):
        with patch("app.report_builder.pdf_converter.html_to_pdf", return_value=mock_pdf):
            response = client.get("/api/report/validpdf/download")
    
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF-1.")


def test_frontend_button_exists():
    """renderReportCard() содержит кнопку "Скачать PDF"."""
    import re
    
    chat_inline_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "theme", "chat-inline.php"
    )
    
    with open(chat_inline_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Проверяем что renderReportCard содержит:
    # 1. .report-ready-actions (контейнер для двух кнопок)
    assert "report-ready-actions" in content
    
    # 2. Кнопку "Скачать PDF"
    assert "Скачать PDF" in content
    
    # 3. Ссылку на /api/report/${slug}/download
    assert "/api/report/" in content
    assert "/download" in content
    
    # 4. CSS класс .report-ready-download
    assert ".report-ready-download" in content
    
    # 5. Emoji 📥 для кнопки скачивания
    assert "📥" in content
