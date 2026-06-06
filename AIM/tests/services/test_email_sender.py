"""Tests for EmailSender service."""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Add AIM/src to path
aim_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(aim_src))

from src.aim.services.email_sender import EmailSender, EmailConfig


class TestEmailSender:
    """Test EmailSender class."""

    def test_email_sender_initialization(self):
        """Test EmailSender initialization."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency",
            reply_to="support@iamaim.ru"
        )

        assert sender.api_key == "SG.test_key"
        assert sender.from_email == "reports@iamaim.ru"
        assert sender.from_name == "AIM Agency"
        assert sender.reply_to == "support@iamaim.ru"
        assert sender.client is not None

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_report_success(self, mock_sendgrid):
        """Test successful report sending."""
        # Mock SendGrid response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "test-message-id-123"}

        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        # Create test PDF
        pdf_bytes = b"%PDF-1.4 test content"

        # Send report
        result = await sender.send_report(
            to_email="client@example.com",
            to_name="John Doe",
            subject="Weekly Report",
            pdf_bytes=pdf_bytes,
            pdf_filename="report.pdf",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        assert result["success"] is True
        assert result["message_id"] == "test-message-id-123"
        assert result["status_code"] == 202

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_report_failure(self, mock_sendgrid):
        """Test report sending failure."""
        # Mock SendGrid error
        mock_client = Mock()
        mock_client.send.side_effect = Exception("SendGrid API error")
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        pdf_bytes = b"%PDF-1.4 test content"

        result = await sender.send_report(
            to_email="client@example.com",
            to_name="John Doe",
            subject="Weekly Report",
            pdf_bytes=pdf_bytes,
            pdf_filename="report.pdf",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        assert result["success"] is False
        assert "SendGrid API error" in result["error"]

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_report_with_additional_message(self, mock_sendgrid):
        """Test sending report with additional message."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "test-id"}

        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        pdf_bytes = b"%PDF-1.4 test content"

        result = await sender.send_report(
            to_email="client@example.com",
            to_name="John Doe",
            subject="Weekly Report",
            pdf_bytes=pdf_bytes,
            pdf_filename="report.pdf",
            project_name="SEO Audit",
            period="May 8-15, 2026",
            additional_message="Great progress this week!"
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_bulk_reports(self, mock_sendgrid):
        """Test sending reports to multiple recipients."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "test-id"}

        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        recipients = [
            {"email": "client1@example.com", "name": "Client 1"},
            {"email": "client2@example.com", "name": "Client 2"},
            {"email": "client3@example.com", "name": "Client 3"},
        ]

        pdf_bytes = b"%PDF-1.4 test content"

        result = await sender.send_bulk_reports(
            recipients=recipients,
            pdf_bytes=pdf_bytes,
            pdf_filename="report.pdf",
            subject_template="Weekly Report for {name}",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        assert result["total"] == 3
        assert result["success"] == 3
        assert result["failed"] == 0
        assert len(result["failures"]) == 0

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_bulk_reports_with_failures(self, mock_sendgrid):
        """Test bulk sending with some failures."""
        # Mock mixed success/failure
        call_count = [0]

        def mock_send(message):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call fails
                raise Exception("SendGrid error")

            mock_response = Mock()
            mock_response.status_code = 202
            mock_response.headers = {"X-Message-Id": f"test-id-{call_count[0]}"}
            return mock_response

        mock_client = Mock()
        mock_client.send.side_effect = mock_send
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        recipients = [
            {"email": "client1@example.com", "name": "Client 1"},
            {"email": "client2@example.com", "name": "Client 2"},
            {"email": "client3@example.com", "name": "Client 3"},
        ]

        pdf_bytes = b"%PDF-1.4 test content"

        result = await sender.send_bulk_reports(
            recipients=recipients,
            pdf_bytes=pdf_bytes,
            pdf_filename="report.pdf",
            subject_template="Weekly Report",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        assert result["total"] == 3
        assert result["success"] == 2
        assert result["failed"] == 1
        assert len(result["failures"]) == 1
        assert result["failures"][0]["email"] == "client2@example.com"

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_send_test_email(self, mock_sendgrid):
        """Test sending test email."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "test-id"}

        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        result = await sender.send_test_email(
            to_email="test@example.com",
            to_name="Test User"
        )

        assert result["success"] is True
        assert result["message_id"] == "test-id"
        assert result["status_code"] == 202

    def test_create_html_content(self):
        """Test HTML content creation."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        html = sender._create_html_content(
            recipient_name="John Doe",
            project_name="SEO Audit",
            period="May 8-15, 2026",
            additional_message="Great work!"
        )

        assert "John Doe" in html
        assert "SEO Audit" in html
        assert "May 8-15, 2026" in html
        assert "Great work!" in html
        assert "AIM Agency" in html

    def test_create_html_content_without_additional_message(self):
        """Test HTML content creation without additional message."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        html = sender._create_html_content(
            recipient_name="Jane Smith",
            project_name="Content Strategy",
            period="May 1-15, 2026"
        )

        assert "Jane Smith" in html
        assert "Content Strategy" in html
        assert "May 1-15, 2026" in html

    def test_create_attachment(self):
        """Test PDF attachment creation."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        pdf_bytes = b"%PDF-1.4 test content"
        attachment = sender._create_attachment(pdf_bytes, "report.pdf")

        assert attachment is not None
        assert attachment.file_name.get() == "report.pdf"
        assert attachment.file_type.get() == "application/pdf"
        assert attachment.disposition.get() == "attachment"

    def test_default_reply_to(self):
        """Test default reply-to uses from_email."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        assert sender.reply_to == "reports@iamaim.ru"

    def test_custom_reply_to(self):
        """Test custom reply-to address."""
        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency",
            reply_to="support@iamaim.ru"
        )

        assert sender.reply_to == "support@iamaim.ru"

    @pytest.mark.asyncio
    @patch('aim.services.email_sender.SendGridAPIClient')
    async def test_large_pdf_attachment(self, mock_sendgrid):
        """Test sending email with large PDF attachment."""
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "test-id"}

        mock_client = Mock()
        mock_client.send.return_value = mock_response
        mock_sendgrid.return_value = mock_client

        sender = EmailSender(
            api_key="SG.test_key",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        # Create large PDF (1MB)
        pdf_bytes = b"%PDF-1.4" + b"x" * (1024 * 1024)

        result = await sender.send_report(
            to_email="client@example.com",
            to_name="John Doe",
            subject="Large Report",
            pdf_bytes=pdf_bytes,
            pdf_filename="large_report.pdf",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        assert result["success"] is True
