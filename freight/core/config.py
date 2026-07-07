"""
Application configuration.

Loads all environment variables from the project's `.env` file and exposes
them through a single `settings` instance. Every component in the application
should import configuration from here instead of reading environment variables
directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines all runtime configuration required by Freight.

    Values are automatically loaded from the `.env` file and validated by
    Pydantic at startup.
    """

    POSTGRES_URL: str
    REDIS_URL: str

    SECRET_KEY: str
    GITHUB_WEBHOOK_SECRET: str
    FERNET_KEY: str

    ARTIFACT_ROOT: str
    LOG_ROOT: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
"""
Global application settings.

Import this object anywhere configuration is required.
"""