from pathlib import Path

from pydantic import BaseModel

from starbug.kube.list import List
from starbug.kube.namespace import Namespace
from starbug.kube.utils import create_kube_object
from starbug.templates.devops.kiroshi import Kiroshi
from starbug.templates.essential.binkcore import Binkcore
from starbug.templates.essential.bootstrapdb import BootstrapDB
from starbug.templates.essential.postgres import Postgres
from starbug.templates.essential.rabbitmq import RabbitMQ
from starbug.templates.essential.redis import Redis
from starbug.templates.tests.kiroshi import TestComponentKiroshi


class Components(BaseModel):
    """Components Required for Testing.

    Args:
        name (str): Name of a component, example "hermes" or "harmonia".
        image (str, optional): An image override, defaults to using Production
            or best next candidate.
    """

    name: str
    image: str | None = None


class SpecTest(BaseModel):
    """New Test Specification.

    Args:
        components list[Components]: A list of components to test, example ["hermes:latest", "midas:latest"]
    """

    components: list[Components]


component_index = {
    "postgres": Postgres,
    "redis": Redis,
    "rabbitmq": RabbitMQ,
    "bootstrapdb": BootstrapDB,
    "kiroshi": Kiroshi,
}

test_index = {
    "kiroshi": TestComponentKiroshi,
}

def create_test(components: Components) -> dict:
    namespace = Namespace()
    test_id = namespace.metadata.name.split("-")[-1]
    items = [
        namespace,
        *Binkcore(namespace=namespace.metadata.name),
    ]
    for component in components:
        resource = component_index[component.name]
        items.extend(resource(namespace=namespace.metadata.name, image=component.image))
    create_kube_object(List(items=items).model_dump(by_alias=True))
    if Path("/mnt/reports").exists():
        Path(f"/mnt/reports/{test_id}").mkdir()
    return {"test_id": test_id, "namespace": namespace.metadata.name}
