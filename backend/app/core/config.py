import re
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_bool_flag(value: Any) -> bool:
    """يقبل true/1/yes (بلا حساسية لحالة الأحرف)؛ أي شيء آخر = False."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "1", "yes")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql://albayan_user:albayan_password@localhost:5434/albayan"
    )
    clerk_secret_key: str = ""
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://albayan-journal.org"
    # مفتاح خادمي صريح حتى لا تؤدي قيمة FRONTEND_BASE_URL الافتراضية إلى تفعيل البريد.
    email_enabled: bool = False
    resend_api_key: SecretStr = SecretStr("")
    email_from: str = ""
    email_reply_to: str = ""
    resend_welcome_template_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "RESEND_WELCOME_TEMPLATE", "RESEND_WELCOME_TEMPLATE_ID"
        ),
    )
    email_asset_base_url: str = ""
    frontend_base_url: str = "http://localhost:3000"
    compiler_url: str = ""
    butex_worker_url: str = ""
    butex_worker_token: str = ""
    # من DEV_MODE — يفعّل أدوات التشخيص (مثل compile.log)؛ لا تفعّله في الإنتاج.
    dev_mode: bool = False

    # من MCP_ENABLED — يفعّل وكلاء MCP (مفاتيح الوكيل، مصادقة alb_، مسارات /wukala).
    mcp_enabled: bool = False

    # من MCP_RESOURCE_URL — عنوان مورد MCP العام (نفس قيمة خادم mcp_server).
    # توكنات OAuth من وكلاء MCP تحمل aud بهذه القيمة؛ بها نميّزها عن جلسات المتصفح.
    mcp_resource_url: str = ""

    @field_validator("dev_mode", "mcp_enabled", "email_enabled", mode="before")
    @classmethod
    def validate_bool_flags(cls, value: Any) -> bool:
        return _parse_bool_flag(value)

    @model_validator(mode="after")
    def validate_email_configuration(self) -> "Settings":
        """يتحقق من إعدادات البريد كوحدة واحدة عند تفعيل الخدمة خادمياً."""
        if not self.email_enabled:
            return self

        required = {
            "RESEND_API_KEY": self.resend_api_key.get_secret_value(),
            "EMAIL_FROM": self.email_from,
            "EMAIL_REPLY_TO": self.email_reply_to,
            "RESEND_WELCOME_TEMPLATE": self.resend_welcome_template_id,
            "FRONTEND_BASE_URL": self.frontend_base_url,
            "EMAIL_ASSET_BASE_URL": self.email_asset_base_url,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Missing required email settings: {', '.join(missing)}")

        self.email_from = _validate_mailbox(self.email_from, "EMAIL_FROM")
        self.email_reply_to = _validate_mailbox(
            self.email_reply_to, "EMAIL_REPLY_TO"
        )
        self.frontend_base_url = _validate_email_url(
            self.frontend_base_url, "FRONTEND_BASE_URL", self.dev_mode
        )
        self.email_asset_base_url = _validate_email_url(
            self.email_asset_base_url, "EMAIL_ASSET_BASE_URL", self.dev_mode
        )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


_EMAIL_ADDRESS_RE = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)


def _validate_mailbox(value: str, setting_name: str) -> str:
    value = value.strip()
    if "\n" in value or "\r" in value:
        raise ValueError(f"{setting_name} must be a valid mailbox identity")
    display_name, address = parseaddr(value)
    has_brackets = "<" in value or ">" in value
    if (
        not _EMAIL_ADDRESS_RE.fullmatch(address)
        or (has_brackets and not (display_name and value.endswith(">")))
        or (not has_brackets and address != value)
    ):
        raise ValueError(f"{setting_name} must be a valid mailbox identity")
    return value


def _validate_email_url(value: str, setting_name: str, dev_mode: bool) -> str:
    value = value.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL")
    if parsed.scheme != "https":
        is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if not dev_mode or not is_local:
            raise ValueError(
                f"{setting_name} must use HTTPS outside local development"
            )
    return value


settings = Settings()
