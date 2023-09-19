"""Settings for the Starbug application."""

from typing import Annotated, ClassVar
from uuid import UUID

from pydantic import HttpUrl, PlainValidator, PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the Starbug application."""

    database_dsn: Annotated[
        str,
        PlainValidator(lambda value: PostgresDsn(value).unicode_string()),
    ] = "postgresql+psycopg://postgres@localhost:5432/postgres"
    redis_dsn: str = "redis://localhost:6379/0"


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
