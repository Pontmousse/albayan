from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    albayan_api_url: str = "http://localhost:8000"
    albayan_agent_token: str = ""
    clerk_issuer_url: str = ""
    mcp_resource_url: str = "http://localhost:8080/mcp"
    host: str = "0.0.0.0"
    port: int = 8080

    @property
    def oauth_enabled(self) -> bool:
        return bool(self.clerk_issuer_url.strip() and self.mcp_resource_url.strip())


settings = Settings()
