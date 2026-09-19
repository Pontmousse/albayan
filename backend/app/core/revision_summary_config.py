from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RevisionSummarySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_model: str = "openrouter/free"


revision_summary_settings = RevisionSummarySettings()
