import os
from dotenv import load_dotenv

load_dotenv()


def _first_env(*names: str, default: str = "") -> str:
    """Return the first non-empty env var value from the provided aliases."""
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return default


def _env_int(*names: str, default: int) -> int:
    value = _first_env(*names, default=str(default))
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_bool(*names: str, default: bool) -> bool:
    value = _first_env(*names, default=str(default))
    return str(value).lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self):
        # ── LLM APIs ───────────────────────────────────────────────────
        self.OPENAI_API_KEY = _first_env("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = _first_env("ANTHROPIC_API_KEY")
        self.DEEPSEEK_API_KEY = _first_env("DEEPSEEK_API_KEY")

        # ── AWS (for data sources) ─────────────────────────────────────
        self.AWS_ACCESS_KEY_ID = _first_env("AWS_ACCESS_KEY_ID")
        self.AWS_SECRET_ACCESS_KEY = _first_env("AWS_SECRET_ACCESS_KEY")

        # ── Supabase (database) ────────────────────────────────────────
        self.SUPABASE_URL = _first_env("SUPABASE_URL")
        # 支持多种API Key命名方式（优先级：SUPABASE_API_KEY > SUPABASE_SERVICE_ROLE_KEY > SUPABASE_KEY）
        self.SUPABASE_KEY = _first_env(
            "SUPABASE_API_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_KEY",
        )
        self.SUPABASE_PASSWORD = _first_env("SUPABASE_PASSWORD")

        # ── Email (for notifications) ──────────────────────────────────
        self.SMTP_HOST = _first_env("SMTP_HOST", "SMTP_SERVER", default="smtp.gmail.com")
        self.SMTP_PORT = _env_int("SMTP_PORT", default=587)
        self.SMTP_USER = _first_env("SMTP_USER", "SMTP_USERNAME")
        self.SMTP_PASSWORD = _first_env("SMTP_PASSWORD")
        self.EMAIL_FROM = _first_env(
            "EMAIL_FROM",
            "MAIL_FROM_ADDRESS",
            default="noreply@esg-system.com",
        )

        # ── Scheduler config ───────────────────────────────────────────
        self.SCAN_INTERVAL_MINUTES = _env_int(
            "SCAN_INTERVAL_MINUTES",
            "SCANNER_INTERVAL",
            default=30,
        )
        self.MAX_SCAN_RESULTS = _env_int("MAX_SCAN_RESULTS", default=100)

        # ── API Keys for data sources ──────────────────────────────────
        self.ALPHA_VANTAGE_KEY = _first_env(
            "ALPHA_VANTAGE_KEY",
            "ALPHA_VANTAGE_API_KEY",
        )
        self.NEWS_API_KEY = _first_env("NEWS_API_KEY", "NEWSAPI_KEY")

        # ── Debug mode ─────────────────────────────────────────────────
        self.DEBUG = _env_bool("DEBUG", default=True)

   
