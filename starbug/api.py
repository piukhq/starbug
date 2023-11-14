"""API Endpoints for Starbug."""

from io import BytesIO

import kr8s
from azure.storage.blob import BlobServiceClient
from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from starbug.kubernetes.custom.resources import StarbugTest
from starbug.namegen import generate_name
from starbug.settings import settings

api = FastAPI()


class Results(BaseModel):
    """Update the results for a test."""

    filename: str
    exit_code: int


class DeploySpec(BaseModel):
    """Spec for a Deployment."""

    name: str
    image: str | None = None


class TestSpec(BaseModel):
    """Spec for a Test."""

    name: str


class JobSpec(BaseModel):
    """Spec for creating a test."""

    name: str = Field(default_factory=lambda: generate_name())
    infrastructure: list[DeploySpec]
    applications: list[DeploySpec]
    test: TestSpec


@api.post("/create")
def create(spec: JobSpec) -> JSONResponse:
    """Create a test."""
    payload = spec.model_dump(exclude_none=True)
    StarbugTest(
        {
            "apiVersion": "bink.com/v1",
            "kind": "StarbugTest",
            "metadata": {"name": payload["name"], "namespace": "starbug"},
            "spec": {
                "infrastructure": payload["infrastructure"],
                "applications": payload["applications"],
                "test": payload["test"],
            },
        },
    ).create()
    return JSONResponse(content={"name": payload["name"]}, status_code=status.HTTP_201_CREATED)


@api.get("/status")
def get_status(name: str | None = None) -> JSONResponse:
    """Get the status of either a single or all tests."""
    if name:
        try:
            test = StarbugTest({"metadata": {"name": name, "namespace": "starbug"}})
            test.refresh()
            response = {"name": test.name, "status": {"phase": test.status.phase, "results": test.status.results}}
        except kr8s._exceptions.NotFoundError:  # noqa: SLF001
            return JSONResponse(content={"error": "Not Found"}, status_code=status.HTTP_404_NOT_FOUND)
    else:
        response = [
            {
                "name": test.name,
                "status": {
                    "phase": test.status.phase,
                    "results": test.status.results,
                },
            }
            for test in kr8s.get("tests", namespace="starbug")
        ]
    return JSONResponse(content=response, status_code=status.HTTP_200_OK)


@api.post("/results/{name}")
def post_results(name: str, results: Results) -> Response:
    """Update the status.results field for a test."""
    result_url = f"https://starbug.ait.gb.bink.com/results/{results.filename}"
    test = StarbugTest({"metadata": {"name": name, "namespace": "starbug"}})
    test.patch({"status": {"results": result_url, "phase": "Completed" if results.exit_code == 0 else "Failed"}})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@api.get("/results/{namespace}/{filename}")
def get_results(namespace: str, filename: str) -> HTMLResponse:
    """Get the results for a test."""
    blob_name = f"{namespace}/{filename}"
    client = BlobServiceClient.from_connection_string(settings.storage_account_dsn)
    blob = client.get_blob_client(container=settings.storage_account_container, blob=blob_name)
    stream = BytesIO()
    blob.download_blob().readinto(stream)
    stream.seek(0)
    return HTMLResponse(content=stream.read(), status_code=status.HTTP_200_OK)
