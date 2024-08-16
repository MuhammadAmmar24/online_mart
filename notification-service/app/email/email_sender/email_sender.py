import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app import settings

logger = logging.getLogger(__name__)


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        logger.info(f"Connecting to SMTP server: {settings.SMTP_SERVER}")
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        logger.info(f"Successfully logged in as {settings.SMTP_USERNAME}")
        text = msg.as_string()
        server.sendmail(settings.SMTP_USERNAME, recipient_email, text)
        server.quit()

        logger.info(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        return False

