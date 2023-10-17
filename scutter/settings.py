"""Scutter settings."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the scutter application."""

    storage_account_dsn: str
    storage_account_container: str = "results"
    file_path: Path = Path("/mnt/results/report.html")


settings = Settings()
