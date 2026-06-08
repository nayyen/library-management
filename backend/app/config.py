"""Typed environment configuration via pydantic-settings.

Loads `.env` (gitignored) into a validated `Settings` class — see CLAUDE.md
"Stack Patterns by Variant" and the locked decision against scattered
`os.environ.get()` calls.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://library:library@db:5432/library"

    # Auth / tokens
    SECRET_KEY: str = "change-me-in-production"
    LIBRARIAN_SIGNUP_CODE: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 60

    # Frontend / cookies
    FRONTEND_URL: str = "http://localhost:5173"
    COOKIE_SECURE: bool = False

    # Mail (Mailpit in dev — see CLAUDE.md "What NOT to Use" re: MailHog/sync SMTP)
    MAIL_SERVER: str = "mailpit"
    MAIL_PORT: int = 1025
    MAIL_FROM: str = "noreply@library.local"
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = False


settings = Settings()
