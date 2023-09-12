"""Scutter Main Module."""

import sys
from pathlib import Path

import inotify.adapters
from azure.storage.blob import BlobServiceClient
from loguru import logger

from scutter.settings import settings


class Scutter:
    """Scutter Class."""

    def __init__(self, path: str) -> None:
        """Initialize the Scutter class."""
        self.blob_service_client = BlobServiceClient.from_connection_string(settings.storage_account_dsn)
        self.container_client = self.blob_service_client.get_container_client(settings.storage_account_container)
        self.path = Path(path)
        self.inotify = inotify.adapters.Inotify()

    def upload_file(self, filename: str) -> None:
        """Upload a file to Azure Blob Storage."""
        full_path = self.path / filename
        logger.info(f"Uploading file: {full_path}")
        with full_path.open("rb") as data:
            self.container_client.upload_blob(name=filename, data=data)
        sys.exit(0)

    def run(self) -> None:
        """Run the Scutter."""
        self.inotify.add_watch(str(self.path))

        for event in self.inotify.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event

            if "IN_CLOSE_WRITE" in type_names:
                self.upload_file(filename)
