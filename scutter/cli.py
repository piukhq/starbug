"""Scutter CLI Entrypoint."""

from pathlib import Path

import click

from scutter.main import Scutter


@click.command()
@click.option("--path", "-p", help="path + filename to upload", default="/mnt/results/report.html")
def cli(path: Path) -> None:
    """Scutter: A helper application that waits for files and then uploads them to Azure Blob Storage."""
    s = Scutter(path)
    s.run()
