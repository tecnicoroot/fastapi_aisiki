from email.message import EmailMessage

import aiosmtplib

from fastapi_aisiki.core.config import settings


async def send_email(*, to: str, subject: str, text: str, html: str | None = None) -> None:
    message = EmailMessage()
    message["From"] = settings.SMTP_FROM
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD.get_secret_value() if settings.SMTP_PASSWORD else None,
        start_tls=settings.SMTP_STARTTLS,
        use_tls=settings.SMTP_SSL,
    )
