"""Email service — async, fire-and-forget via FastAPI BackgroundTasks.

Per 01-RESEARCH.md Pattern 5 + CLAUDE.md "What NOT to Use":
  - fastapi-mail backed by Mailpit in dev (MAIL_SERVER="mailpit", port 1025,
    no TLS/credentials — plain SMTP capture).
  - `send_reset_email` is always called via `background_tasks.add_task`, NEVER
    awaited directly in a request handler (T-01-03-SMTPBLOCK: blocking SMTP
    in the request path is the anti-pattern).
  - Template folder is `app/templates/email` — Jinja2 HTML templates.
"""

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.config import settings

_conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER="app/templates/email",
)


async def send_reset_email(email: str, reset_link: str) -> None:
    """Send a password-reset email containing a single-use link.

    Called via `background_tasks.add_task(send_reset_email, ...)` so the
    HTTP response is never blocked waiting on SMTP round-trip latency.
    """
    message = MessageSchema(
        subject="Reset your library password",
        recipients=[email],
        template_body={"reset_link": reset_link, "expires_in": "1 hour"},
        subtype=MessageType.html,
    )
    fm = FastMail(_conf)
    await fm.send_message(message, template_name="password_reset.html")
