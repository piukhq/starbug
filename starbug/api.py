"""API Endpoints for Starbug."""

from fastapi import FastAPI, status

from starbug.logic.api import create_test, list_test, get_test, delete_test, purge_test
from starbug.models.api import SpecTest

api = FastAPI()


@api.get("/test", status_code=status.HTTP_200_OK)
def api_list_test() -> list:
    """Get a list of all tests."""
    return list_test()

@api.get("/test/{test_id}", status_code=status.HTTP_200_OK)
def api_get_test(test_id: str) -> dict:
    """Get a test."""
    return get_test(test_id=test_id)

@api.delete("/test/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
def api_delete_test(test_id: str) -> None:
    """Delete a test."""
    delete_test(test_id=test_id)

@api.delete("/test/{test_id}/purge", status_code=status.HTTP_204_NO_CONTENT)
def api_purge_test(test_id: str) -> None:
    """Purge a Test."""
    purge_test(test_id=test_id)

@api.post("/test", status_code=status.HTTP_201_CREATED)
def post_test(spec: SpecTest) -> dict:
    """Create a new Test."""
    return create_test(spec=spec)
