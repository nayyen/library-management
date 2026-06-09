"""Email service — async, fire-and-forget via FastAPI BackgroundTasks.

Per 01-RESEARCH.md Pattern 5 + CLAUDE.md "What NOT to Use":
  - fastapi-mail backed by Mailpit in dev (MAIL_SERVER="mailpit", port 1025,
    no TLS/credentials — plain SMTP capture).
  - `send_reset_email` is always called via `background_tasks.add_task`, NEVER
    awaited directly in a request handler (T-01-03-SMTPBLOCK: blocking SMTP
    in the request path is the anti-pattern).
  - TEMPLATE_FOLDER uses an absolute path derived from __file__ so it resolves
    correctly regardless of CWD (avoids Docker vs. local CWD divergence with
    Pydantic's DirectoryPath validation).
"""

import logging
from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import settings

logger = logging.getLogger(__name__)

# Absolute path — reliable regardless of where uvicorn is invoked from.
# In Docker (WORKDIR=/app): __file__ = /app/app/services/email_service.py
# → .parent.parent = /app/app → / "templates" / "email" = /app/app/templates/email
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"

_conf = ConnectionConfig(
    MAIL_USERNAME="",            # Mailpit needs no SMTP auth — explicit empty
    MAIL_PASSWORD="",            # Mailpit needs no SMTP auth — explicit empty
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=False,       # Mailpit never uses SMTP AUTH
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=_TEMPLATE_DIR,
)


async def send_reset_email(email: str, reset_link: str) -> None:
    """Send a password-reset email containing a single-use link.

    Called via `background_tasks.add_task(send_reset_email, ...)` so the
    HTTP response is never blocked waiting on SMTP round-trip latency.
    Exceptions are caught and logged so a broken mail server never silently
    swallows the failure — check the backend logs if emails don't arrive.
    """
    try:
        message = MessageSchema(
            subject="Reset your library password",
            recipients=[email],
            template_body={"reset_link": reset_link, "expires_in": "1 hour"},
            subtype=MessageType.html,
        )
        fm = FastMail(_conf)
        await fm.send_message(message, template_name="password_reset.html")
        logger.info("Password-reset email sent to %s", email)
    except Exception:
        logger.exception("Failed to send password-reset email to %s", email)
