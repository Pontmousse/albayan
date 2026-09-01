import re
from email.utils import parseaddr
from typing import Any
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator, model_validator
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
    clerk_webhook_signing_secret: str = ""
    s3_bucket: str = ""
    s3_endpoint_url: str = ""
    s3_access_key: str = ""
    s3_secret_key: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://albayan-journal.org"
    resend_api_key: SecretStr = SecretStr("")
    email_from: str = ""
    email_reply_to: str = ""
    resend_welcome_template: str = ""
    resend_app_invitation_template: str = ""
    resend_auth_verification_template: str = ""
    resend_password_reset_template: str = ""
    resend_submission_received_template: str = ""
    resend_new_submission_alert_template: str = ""
    resend_editor_assigned_template: str = ""
    resend_review_invitation_template: str = ""
    resend_reviewer_assigned_template: str = ""
    resend_review_reminder_template: str = ""
    resend_review_submitted_template: str = ""
    resend_decision_template: str = ""
    resend_article_published_template: str = ""
    resend_unread_notifications_digest_template: str = ""
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

    @field_validator("dev_mode", "mcp_enabled", mode="before")
    @classmethod
    def validate_bool_flags(cls, value: Any) -> bool:
        return _parse_bool_flag(value)

    @model_validator(mode="after")
    def validate_email_configuration(self) -> "Settings":
        """Validate the server-only email settings together when configured."""
        api_key = self.resend_api_key.get_secret_value()
        email_settings = {
            "RESEND_API_KEY": api_key,
            "EMAIL_FROM": self.email_from,
            "EMAIL_REPLY_TO": self.email_reply_to,
            "RESEND_WELCOME_TEMPLATE": self.resend_welcome_template,
            "RESEND_APP_INVITATION_TEMPLATE": self.resend_app_invitation_template,
            "RESEND_AUTH_VERIFICATION_TEMPLATE": (
                self.resend_auth_verification_template
            ),
            "RESEND_PASSWORD_RESET_TEMPLATE": self.resend_password_reset_template,
            "RESEND_SUBMISSION_RECEIVED_TEMPLATE": (
                self.resend_submission_received_template
            ),
            "RESEND_NEW_SUBMISSION_ALERT_TEMPLATE": (
                self.resend_new_submission_alert_template
            ),
            "RESEND_EDITOR_ASSIGNED_TEMPLATE": self.resend_editor_assigned_template,
            "RESEND_REVIEW_INVITATION_TEMPLATE": self.resend_review_invitation_template,
            "RESEND_REVIEWER_ASSIGNED_TEMPLATE": self.resend_reviewer_assigned_template,
            "RESEND_REVIEW_REMINDER_TEMPLATE": self.resend_review_reminder_template,
            "RESEND_REVIEW_SUBMITTED_TEMPLATE": self.resend_review_submitted_template,
            "RESEND_DECISION_TEMPLATE": self.resend_decision_template,
            "RESEND_ARTICLE_PUBLISHED_TEMPLATE": self.resend_article_published_template,
            "RESEND_UNREAD_NOTIFICATIONS_DIGEST_TEMPLATE": (
                self.resend_unread_notifications_digest_template
            ),
        }

        # An entirely empty group disables email locally. Supplying any member
        # opts into email delivery and requires a complete, coherent group.
        if not any(value.strip() for value in email_settings.values()):
            return self

        required = {
            **email_settings,
            "FRONTEND_BASE_URL": self.frontend_base_url,
        }
        missing = [name for name, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(f"Missing required email settings: {', '.join(missing)}")

        if not api_key.startswith("re_"):
            raise ValueError("RESEND_API_KEY must be a Resend API key")

        self.email_from = _validate_mailbox(self.email_from, "EMAIL_FROM")
        self.email_reply_to = _validate_mailbox(
            self.email_reply_to, "EMAIL_REPLY_TO"
        )
        self.resend_welcome_template = self.resend_welcome_template.strip()
        self.resend_app_invitation_template = (
            self.resend_app_invitation_template.strip()
        )
        self.resend_auth_verification_template = (
            self.resend_auth_verification_template.strip()
        )
        self.resend_password_reset_template = self.resend_password_reset_template.strip()
        self.resend_submission_received_template = (
            self.resend_submission_received_template.strip()
        )
        self.resend_new_submission_alert_template = (
            self.resend_new_submission_alert_template.strip()
        )
        self.resend_editor_assigned_template = self.resend_editor_assigned_template.strip()
        self.resend_review_invitation_template = (
            self.resend_review_invitation_template.strip()
        )
        self.resend_reviewer_assigned_template = (
            self.resend_reviewer_assigned_template.strip()
        )
        self.resend_review_reminder_template = (
            self.resend_review_reminder_template.strip()
        )
        self.resend_review_submitted_template = (
            self.resend_review_submitted_template.strip()
        )
        self.resend_decision_template = self.resend_decision_template.strip()
        self.resend_article_published_template = (
            self.resend_article_published_template.strip()
        )
        self.resend_unread_notifications_digest_template = (
            self.resend_unread_notifications_digest_template.strip()
        )
        self.frontend_base_url = _validate_email_url(
            self.frontend_base_url, "FRONTEND_BASE_URL", self.dev_mode
        )
        return self

    @property
    def email_enabled(self) -> bool:
        api_key = (
            self.resend_api_key.get_secret_value()
            if hasattr(self.resend_api_key, "get_secret_value")
            else self.resend_api_key
        )
        return bool(api_key)

    @property
    def email_reply_to_address(self) -> str:
        return parseaddr(self.email_reply_to)[1]

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
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError(f"{setting_name} must be a clean base URL")
    if parsed.scheme != "https":
        is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if not dev_mode or not is_local:
            raise ValueError(
                f"{setting_name} must use HTTPS outside local development"
            )
    return value


settings = Settings()
