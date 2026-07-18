from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_dev_mode(value: Any) -> bool:
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
    frontend_base_url: str = "http://localhost:3000"
    compiler_url: str = ""
    # من DEV_MODE — يفعّل endpoints التشخيص فقط؛ لا تفعّله في الإنتاج.
    dev_mode: bool = False

    @field_validator("dev_mode", mode="before")
    @classmethod
    def validate_dev_mode(cls, value: Any) -> bool:
        return _parse_dev_mode(value)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
