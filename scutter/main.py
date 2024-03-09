"""Scutter Main Module."""

import sys
from pathlib import Path
from sys import platform
from time import sleep

import requests
from azure.storage.blob import BlobServiceClient
from box import Box
from loguru import logger
from pydantic_settings import BaseSettings

if platform == "Darwin":
    logger.info("Running this tool on macOS is not supported.")
    sys.exit(0)


class Settings(BaseSettings):
    """Settings for the scutter application."""

    storage_account_dsn: str
    storage_account_container: str = "results"
    file_path: Path = Path("/mnt/results/report.html")


settings = Settings()


class Scutter:
    """Scutter Class."""

    def __init__(self) -> None:
        """Initialize the Scutter class."""
        self.blob_service_client = BlobServiceClient.from_connection_string(settings.storage_account_dsn)
        self.container_client = self.blob_service_client.get_container_client(settings.storage_account_container)
        self.namespace = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read_text()
        self.token = Path("/var/run/secrets/kubernetes.io/serviceaccount/token").read_text()
        self.hostname = Path("/etc/hostname").read_text().strip()
        self.pod_url = f"https://kubernetes.default:443/api/v1/namespaces/{self.namespace}/pods/{self.hostname}"
        self.results_url = f"http://starbug.starbug/results/{self.namespace}"

    def run(self) -> None:
        """Run the Scutter."""
        while True:
            pod = Box(
                requests.get(
                    self.pod_url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    verify="/var/run/secrets/kubernetes.io/serviceaccount/ca.crt",
                    timeout=10,
                ).json(),
            )
            test_container = [container for container in pod.status.containerStatuses if container.name == "test"][0]  # noqa: RUF015
            try:
                if test_container.state.get("terminated"):
                    exit_code = test_container.state.terminated.exitCode
                    blob_name = f"{self.namespace}/{settings.file_path.name}"
                    data = settings.file_path.read_bytes()
                    logger.info(f"Uploading file: {blob_name}")
                    self.container_client.upload_blob(name=blob_name, data=data)
                    logger.info(f"Uploaded file: {blob_name}")
                    results = {"filename": blob_name, "exit_code": exit_code}
                    logger.info(f"Informing Starbug of results: {results}")
                    requests.post(self.results_url, json=results, timeout=10)
                    break
            except FileNotFoundError:
                logger.info("Test container finished, but the file does not exist.")
                results = {"filename": "None", "exit_code": exit_code}
                requests.post(self.results_url, json=results, timeout=10)
                break
            logger.info("Pod not finished yet, waiting for 10 seconds.")
            sleep(10)
