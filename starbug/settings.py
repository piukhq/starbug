"""Settings for the Starbug application."""

from typing import ClassVar
from uuid import UUID

from pydantic import HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the scutter application."""

    storage_account_dsn: str
    storage_account_container: str = "results"


settings = Settings()


class OIDCSettings(BaseSettings):
    """Settings for OIDC Components."""

    issuer_url: HttpUrl = "https://uksouth.oic.prod-aks.azure.com/a6e2367a-92ea-4e5a-b565-723830bcc095/e9bbbd31-b8e8-4f40-86a9-663186b7fa45/"
    resource_group_name: str = "uksouth-ait"
    subscription_id: UUID = "0b92124d-e5fe-4c9a-a898-1fdf02502e01"
    identities: ClassVar[list[str]] = [
        "angelia",
        "boreas",
        "bullsquid",
        "cosmos",
        "eos",
        "europa",
        "harmonia",
        "hermes",
        "kiroshi",
        "metis",
        "midas",
        "snowstorm",
        "zephyrus",
    ]


oidc_settings = OIDCSettings()
