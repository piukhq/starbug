"""The Starbug Application."""

import typer
from typing_extensions import Annotated

app = typer.Typer()


@app.command()
def server(
    host: Annotated[str, typer.Option(help="Host to run on")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to run on")] = 6502,
) -> None:
    """Start the Starbug API Server."""
    import uvicorn

    uvicorn.run("starbug.api:api", host=host, port=port)


@app.command()
def worker() -> None:
    """Start the Starbug Worker."""
    from starbug.worker import Worker

    worker = Worker()
    worker.get_tests()


@app.command()
def generate(
    name: Annotated[str, typer.Argument(help="Name of the Application")],
    namespace: Annotated[str, typer.Option(help="Namespace to deploy to")] = "default",
) -> None:
    """Generate a Kubernetes Manifest for a nammed application."""
    import yaml

    from starbug.mapping import application_mapping, infrastructure_mapping, test_mapping

    services = {**application_mapping, **infrastructure_mapping, **test_mapping}
    try:
        manifests = [service.raw for service in services[name](namespace=namespace).deploy()]
        typer.echo(yaml.dump_all(manifests))
    except KeyError:
        typer.echo(f"Service {name} not found, supported services: {', '.join(services)}")


@app.command()
def crd() -> None:
    """Print the Starbug Custom Resource Definition."""
    import yaml

    from starbug.kubernetes.internal.crd import starbug_crd

    typer.echo(yaml.dump(starbug_crd.raw))
