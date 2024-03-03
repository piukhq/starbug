"""Scutter Module."""
import typer

app = typer.Typer()


@app.command()
def cli() -> None:
    """Scutter: A helper application that waits for files and then uploads them to Azure Blob Storage."""
    from scutter.main import Scutter

    s = Scutter()
    s.run()
