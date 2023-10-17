"""Scutter settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the scutter application."""

    storage_account_dsn: str
    storage_account_container: str = "results"


settings = Settings()
