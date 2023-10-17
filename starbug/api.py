"""API Endpoints for Starbug."""

from io import BytesIO

from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from starbug.kubernetes.custom.resources import StarbugTest
from starbug.settings import settings

api = FastAPI()


class Results(BaseModel):
    """Update the results for a test."""

    filename: str
    exit_code: int


@api.post("/results/{name}")
def post_results(name: str, results: Results) -> dict:
    """Update the status.results field for a test."""
    result_url = f"https://starbug.ait.gb.bink.com/results/{results.filename}"
    test = StarbugTest({"metadata": {"name": name, "namespace": "starbug"}})
    test.patch({"status": {"results": result_url, "phase": "Completed" if results.exit_code == 0 else "Failed"}})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api.get("/results/{namespace}/{filename}")
def get_results(namespace: str, filename: str) -> dict:
    """Get the results for a test."""
    blob_name = f"{namespace}/{filename}"
    client = BlobServiceClient.from_connection_string(settings.storage_account_dsn)
    blob = client.get_blob_client(container=settings.storage_account_container, blob=blob_name)
    stream = BytesIO()
    blob.download_blob().readinto(stream)
    stream.seek(0)
    return HTMLResponse(content=stream.read(), status_code=status.HTTP_200_OK)
