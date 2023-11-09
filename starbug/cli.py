"""Module containing the command-line interface for Starbug."""

import click
import kr8s
import uvicorn
from click_aliases import ClickAliasedGroup

from starbug.kubernetes.internal.crd import _starbug_crd
from starbug.worker import Worker


@click.group(cls=ClickAliasedGroup)
def cli() -> None:
    """Group for the top-level commands and groups."""


@cli.command(name="server", aliases=["s"])
@click.option("--host", "-h", default="127.0.0.1")
@click.option("--port", "-p", default=6502)
@click.option("--reload", "-r", default=False)
def server(host: str, port: int, reload: bool) -> None:  # noqa: FBT001
    """Start the Starbug server."""
    uvicorn.run("starbug.api:api", host=host, port=port, reload=reload)


@cli.command(name="worker", aliases=["w"])
def worker() -> None:
    """Start the Starbug worker."""
    custom_resources = [resource.metadata.name for resource in kr8s.get("customresourcedefinitions")]
    if "tests.bink.com" not in custom_resources:
        click.echo("Starbug CRD not found. Creating...")
        _starbug_crd().create()
    worker = Worker()
    worker.get_tests()


if __name__ == "__main__":
    cli()
