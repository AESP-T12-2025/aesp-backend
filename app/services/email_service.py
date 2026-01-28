"""
Email Service
=============
Handles sending emails for the application.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_weekly_report_email(to_email: str, html_content: str, subject: str = "Báo cáo hàng tuần AESP"):
    """
    Send HTML email with weekly report.
    """
    try:
        # Email configuration
        smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = getattr(settings, 'SMTP_PORT', 587)
        smtp_username = getattr(settings, 'SMTP_USERNAME', None)
        smtp_password = getattr(settings, 'SMTP_PASSWORD', None)

        if not smtp_username or not smtp_password:
            logger.warning(f"Email config missing, skipping send to {to_email}")
            return False

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = smtp_username
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, to_email, msg.as_string())
        server.quit()

        logger.info(f"✅ Sent weekly report email to {to_email}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        return False