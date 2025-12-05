"""Configuration management for qontinui-web-mcp."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="QONTINUI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_url: str = "http://localhost:8000"
    api_timeout: int = 30

    # Authentication - can use either token or credentials
    access_token: str | None = None
    email: str | None = None
    password: str | None = None

    # Logging
    log_level: str = "INFO"

    @property
    def has_credentials(self) -> bool:
        """Check if credentials are available for login."""
        return bool(self.email and self.password)

    @property
    def has_token(self) -> bool:
        """Check if an access token is available."""
        return bool(self.access_token)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
