"""
Minimal email sender. In development (no SMTP configured) it just logs the
email instead of sending it, so OTP flows are testable without a real
mail provider. Wire in SMTP / SES / SendGrid credentials via .env when ready.
"""
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def send_email(to: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        logger.info("[DEV EMAIL] to=%s subject=%s body=%s", to, subject, body)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, [to], msg.as_string())
