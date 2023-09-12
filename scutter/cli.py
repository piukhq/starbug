"""Scutter CLI Entrypoint."""

import click

from scutter.main import Scutter


@click.command()
@click.option("--path", "-p", help="Path to watch for files", required=True)
def cli(path: str) -> None:
    """Scutter: A helper application for waiting for files, and then moving them to Azure Blob Storage."""
    s = Scutter(path)
    s.run()
