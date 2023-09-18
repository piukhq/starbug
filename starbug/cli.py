"""Module containing the command-line interface for Starbug."""

import click
import uvicorn
from click_aliases import ClickAliasedGroup
from tabulate import tabulate


@click.group(cls=ClickAliasedGroup)
def cli() -> None:
    """Group for the top-level commands and groups."""


@cli.command(name="server", aliases=["s"])
@click.argument("host", default="127.0.0.1")
@click.argument("port", default=6502)
def server(host: str, port: int) -> None:
    """Start the Starbug server."""
    uvicorn.run("starbug.api:api", host=host, port=port)


@cli.group(name="get", aliases=["g"], cls=ClickAliasedGroup)
def get() -> None:
    """Group for the get commands."""

@get.command(name="jobs", aliases=["j", "job"])
def get_jobs() -> None:
    """Get a list of jobs."""
    table = [
        ("abc123", "Pending", "1s"),
        ("def456", "Running", "1h"),
        ("ghi789", "Complete", "2d"),
    ]
    click.echo(tabulate(table, headers=["Name", "Status", "Age"], tablefmt="plain"))

@get.command(name="results", aliases=["r", "result"])
def get_results() -> None:
    """Get the results for a specific job."""
    click.echo("Results for job abc123")

if __name__ == "__main__":
    cli()
