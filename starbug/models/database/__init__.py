"""Database models for Starbug."""
from datetime import datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, declarative_base, mapped_column
from sqlalchemy.sql import func
from sqlalchemy_mixins.serialize import SerializeMixin

from starbug.settings import settings

engine = create_engine(settings.database_dsn)
Base: DeclarativeBase = declarative_base()


class Tests(Base, SerializeMixin):
    """Model representing tests in the database.

    Attributes
        id (str): The ID of the job.
        status (str): The status of the job.
        created_at (datetime): The time the job was created.
        updated_at (datetime): The time the job was last updated.
        report (str): The report of the job.
    """

    __tablename__ = "tests"

    id: Mapped[str] = mapped_column(nullable=False, primary_key=True)  # noqa: A003
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(nullable=True, onupdate=func.now())
    spec: Mapped[dict[str, Any]] = mapped_column(type_=JSONB, nullable=True)
    report: Mapped[str] = mapped_column(nullable=True)
