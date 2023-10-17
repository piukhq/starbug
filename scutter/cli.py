"""Scutter CLI Entrypoint."""

import click

from scutter.main import Scutter


@click.command()
def cli() -> None:
    """Scutter: A helper application that waits for files and then uploads them to Azure Blob Storage."""
    s = Scutter()
    s.run()
