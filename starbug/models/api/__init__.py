"""Models for the API."""

from pydantic import BaseModel


class Resource(BaseModel):
    """Resource to be created.

    Args:
        name (str): Name of a resource, example "hermes" or "harmonia".
        image (str, optional): An image override, defaults to using best candidate.
    """

    name: str
    image: str | None = None


class SpecTest(BaseModel):
    """New Test Specification.

    Args:
        test_id (str, optional): The ID of the test, example "abc123", defaults to a random string.
        infrastructure (list[Resource], optional): A list of infrastructure resources to create,
            example: [{"name": "postgres", "image": "docker.io/postgres:14"}, {"name": "redis"}]
        applications (list[Resource], optional): A list of applications to create,
            example: [{"name": "hermes"}, {"name": "midas"}]
        test_suite (Resource, optional): The test suite to run, example "pyqa"
        timeout (int, optional): The timeout for the test in minutes, defaults to 60.
    """

    test_id: str | None = None
    infrastructure: list[Resource] | None = None
    applications: list[Resource] | None = None
    test_suite: Resource | None = None
    timeout: int | None = 60

class ApiList(BaseModel):
    """List API.

    Args:
        limit (int, optional): The maximum number of results to return, defaults to None.
    """

    limit: int | None = None

class ApiGet(BaseModel):
    """Get API.

    Args:
        test_id (str): The ID of the test to get.
    """

    test_id: str
