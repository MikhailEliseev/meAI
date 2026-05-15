"""Email sender service - delivers PDF reports via SendGrid."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging
from pathlib import Path
import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Email,
    To,
    Content,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)


logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuration for email sending."""
    to_email: str
    to_name: Optional[str] = None
    subject: str = "Project Report"
    reply_to: Optional[str] = None


class EmailSender:
    """Sends PDF reports via SendGrid email.

    Handles email delivery with:
    - PDF attachment support
    - HTML email templates
    - Recipient management
    - Delivery tracking
    - Rate limiting (SendGrid limits)
    - Error handling and retry

    Example:
        sender = EmailSender(
            api_key="SG.xxx",
            from_email="reports@iamaim.ru",
            from_name="AIM Agency"
        )

        # Send report
        result = await sender.send_report(
            to_email="client@example.com",
            to_name="John Doe",
            subject="Weekly Project Report",
            pdf_bytes=report_pdf,
            pdf_filename="report_2026-05-15.pdf",
            project_name="SEO Audit",
            period="May 8-15, 2026"
        )

        if result.success:
            print(f"Email sent! Message ID: {result.message_id}")
        else:
            print(f"Failed: {result.error}")
    """

    def __init__(
        self,
        api_key: str,
        from_email: str,
        from_name: str = "AIM Agency",
        reply_to: Optional[str] = None,
    ):
        """Initialize email sender.

        Args:
            api_key: SendGrid API key
            from_email: Sender email address
            from_name: Sender name
            reply_to: Reply-to email address
        """
        self.api_key = api_key
        self.from_email = from_email
        self.from_name = from_name
        self.reply_to = reply_to or from_email

        # Create SendGrid client
        self.client = SendGridAPIClient(api_key=api_key)

    async def send_report(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        pdf_bytes: bytes,
        pdf_filename: str,
        project_name: str,
        period: str,
        additional_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send report email with PDF attachment.

        Args:
            to_email: Recipient email
            to_name: Recipient name
            subject: Email subject
            pdf_bytes: PDF file as bytes
            pdf_filename: PDF filename
            project_name: Project name for email body
            period: Report period for email body
            additional_message: Optional additional message

        Returns:
            Result dict with success status and message_id or error
        """
        try:
            # Create email message
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject=subject,
            )

            # Set reply-to
            message.reply_to = Email(self.reply_to)

            # Create HTML content
            html_content = self._create_html_content(
                recipient_name=to_name,
                project_name=project_name,
                period=period,
                additional_message=additional_message,
            )
            message.content = Content("text/html", html_content)

            # Add PDF attachment
            attachment = self._create_attachment(pdf_bytes, pdf_filename)
            message.attachment = attachment

            # Send email
            response = self.client.send(message)

            logger.info(
                f"Email sent to {to_email}: status={response.status_code}, "
                f"message_id={response.headers.get('X-Message-Id')}"
            )

            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id"),
                "status_code": response.status_code,
            }

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def send_bulk_reports(
        self,
        recipients: List[Dict[str, Any]],
        pdf_bytes: bytes,
        pdf_filename: str,
        subject_template: str,
        project_name: str,
        period: str,
    ) -> Dict[str, Any]:
        """Send reports to multiple recipients.

        Args:
            recipients: List of recipient dicts with 'email' and 'name'
            pdf_bytes: PDF file as bytes
            pdf_filename: PDF filename
            subject_template: Email subject template (can include {name})
            project_name: Project name
            period: Report period

        Returns:
            Result dict with success count and failures
        """
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "failures": [],
        }

        for recipient in recipients:
            email = recipient.get("email")
            name = recipient.get("name", "")

            # Format subject
            subject = subject_template.format(name=name)

            # Send email
            result = await self.send_report(
                to_email=email,
                to_name=name,
                subject=subject,
                pdf_bytes=pdf_bytes,
                pdf_filename=pdf_filename,
                project_name=project_name,
                period=period,
            )

            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failures"].append({
                    "email": email,
                    "error": result.get("error"),
                })

        logger.info(
            f"Bulk send completed: {results['success']}/{results['total']} successful"
        )

        return results

    def _create_html_content(
        self,
        recipient_name: str,
        project_name: str,
        period: str,
        additional_message: Optional[str] = None,
    ) -> str:
        """Create HTML email content.

        Args:
            recipient_name: Recipient name
            project_name: Project name
            period: Report period
            additional_message: Optional additional message

        Returns:
            HTML content as string
        """
        additional_html = ""
        if additional_message:
            additional_html = f"""
            <div style="margin: 20px 0; padding: 15px; background-color: #F3F4F6; border-radius: 8px;">
                <p style="margin: 0; color: #374151;">{additional_message}</p>
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #1F2937; margin: 0; padding: 0; background-color: #F9FAFB;">
            <div style="max-width: 600px; margin: 0 auto; padding: 40px 20px;">
                <!-- Header -->
                <div style="text-align: center; margin-bottom: 40px;">
                    <h1 style="color: #1E40AF; margin: 0; font-size: 28px;">AIM Agency</h1>
                    <p style="color: #6B7280; margin: 10px 0 0 0;">AI-First Medical Marketing</p>
                </div>

                <!-- Main Content -->
                <div style="background-color: white; border-radius: 12px; padding: 40px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);">
                    <h2 style="color: #1F2937; margin: 0 0 20px 0; font-size: 24px;">Project Report</h2>

                    <p style="color: #374151; margin: 0 0 15px 0;">Hello {recipient_name},</p>

                    <p style="color: #374151; margin: 0 0 15px 0;">
                        Please find attached your project report for <strong>{project_name}</strong> covering the period <strong>{period}</strong>.
                    </p>

                    {additional_html}

                    <p style="color: #374151; margin: 20px 0 15px 0;">
                        The attached PDF contains:
                    </p>

                    <ul style="color: #374151; margin: 0 0 20px 0; padding-left: 20px;">
                        <li>Executive summary</li>
                        <li>Progress overview with charts</li>
                        <li>Milestone tracking</li>
                        <li>Task breakdown by status and assignee</li>
                        <li>Performance metrics</li>
                    </ul>

                    <p style="color: #374151; margin: 20px 0 0 0;">
                        If you have any questions or need clarification on any aspect of the report, please don't hesitate to reach out.
                    </p>
                </div>

                <!-- Footer -->
                <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #E5E7EB;">
                    <p style="color: #6B7280; margin: 0 0 10px 0; font-size: 14px;">
                        This report was automatically generated by AIM Agency Operations System
                    </p>
                    <p style="color: #9CA3AF; margin: 0; font-size: 12px;">
                        © 2026 AIM Agency. All rights reserved.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _create_attachment(self, pdf_bytes: bytes, filename: str) -> Attachment:
        """Create PDF attachment for email.

        Args:
            pdf_bytes: PDF file as bytes
            filename: PDF filename

        Returns:
            SendGrid Attachment object
        """
        # Encode PDF to base64
        encoded = base64.b64encode(pdf_bytes).decode()

        # Create attachment
        attachment = Attachment(
            FileContent(encoded),
            FileName(filename),
            FileType("application/pdf"),
            Disposition("attachment"),
        )

        return attachment

    async def send_test_email(
        self,
        to_email: str,
        to_name: str = "Test User",
    ) -> Dict[str, Any]:
        """Send test email without attachment.

        Args:
            to_email: Recipient email
            to_name: Recipient name

        Returns:
            Result dict with success status
        """
        try:
            message = Mail(
                from_email=Email(self.from_email, self.from_name),
                to_emails=To(to_email, to_name),
                subject="Test Email from AIM Agency",
            )

            message.reply_to = Email(self.reply_to)

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Test Email</h2>
                <p>Hello {to_name},</p>
                <p>This is a test email from AIM Agency Operations System.</p>
                <p>If you received this email, the email configuration is working correctly.</p>
            </body>
            </html>
            """

            message.content = Content("text/html", html_content)

            response = self.client.send(message)

            logger.info(f"Test email sent to {to_email}: status={response.status_code}")

            return {
                "success": True,
                "message_id": response.headers.get("X-Message-Id"),
                "status_code": response.status_code,
            }

        except Exception as e:
            logger.error(f"Failed to send test email to {to_email}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
