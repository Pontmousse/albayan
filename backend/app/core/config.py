from typing import Any

from pydantic import field_validator
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
    resend_api_key: str = ""
    email_from: str = ""
    resend_welcome_template_id: str = ""
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

    @field_validator("dev_mode", "mcp_enabled", mode="before")
    @classmethod
    def validate_bool_flags(cls, value: Any) -> bool:
        return _parse_bool_flag(value)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
