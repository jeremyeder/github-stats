"""Configuration management using pydantic."""

import logging
from functools import lru_cache

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings."""

    github_token: str = Field(..., env="GITHUB_TOKEN")
    database_url: str = Field(
        "sqlite:///./github_stats.db",
        env="DATABASE_URL"
    )
    log_level: str = Field("WARNING", env="LOG_LEVEL")

    # Email configuration
    smtp_server: str | None = Field(None, env="SMTP_SERVER")
    smtp_port: int = Field(587, env="SMTP_PORT")
    smtp_username: str | None = Field(None, env="SMTP_USERNAME")
    smtp_password: str | None = Field(None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(True, env="SMTP_USE_TLS")

    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def setup_logging() -> None:
    """Configure logging based on settings."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
