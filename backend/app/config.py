"""Settings from environment / backend/.env."""
import os
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:password@localhost:3306/pharmacy_shelf?charset=utf8mb4",
        )
        self.cors_origins = [
            o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
        ]
        self.timezone = os.getenv("TIMEZONE", "Asia/Dhaka")
        self.auto_create_tables = _bool("AUTO_CREATE_TABLES", True)

        self.scheduler_enabled = _bool("SCHEDULER_ENABLED", True)
        self.digest_hour = _int("DIGEST_HOUR", 8)
        self.digest_minute = _int("DIGEST_MINUTE", 0)

        # how many days of sales rows are handed to ai_engine (it computes velocity/forecast itself)
        self.sales_history_days = _int("SALES_HISTORY_DAYS", 120)
        self.default_snooze_days = _int("DEFAULT_SNOOZE_DAYS", 3)
        self.dismiss_days = _int("DISMISS_DAYS", 30)

        self.email_enabled = _bool("EMAIL_ENABLED", False)
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = _int("SMTP_PORT", 587)
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", "") or self.smtp_user
        self.email_to = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]

        self.telegram_enabled = _bool("TELEGRAM_ENABLED", False)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        self.sms_enabled = _bool("SMS_ENABLED", False)
        self.sms_api_url = os.getenv("SMS_API_URL", "")
        self.sms_api_key = os.getenv("SMS_API_KEY", "")
        self.sms_sender_id = os.getenv("SMS_SENDER_ID", "")
        self.sms_to = [n.strip() for n in os.getenv("SMS_TO", "").split(",") if n.strip()]


settings = Settings()


def today_local() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()
