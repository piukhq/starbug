"""Module containing the command-line interface for Starbug."""

import click
import uvicorn

from starbug.client import Client


@click.group()
def cli() -> None:
    """Group for the top-level commands and groups."""


@cli.command(name="api")
def _api_server() -> None:
    uvicorn.run("starbug.api:api", host="127.0.0.1", port=6502)


@cli.command(name="client")
def _api_client() -> None:
    c = Client()
    c.run_job()


if __name__ == "__main__":
    cli()
