"""Kubernetes Logic."""

from time import sleep

from kr8s.objects import Namespace
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from starbug.models.database import Tests, engine
from starbug.models.kubernetes.devops.kiroshi import Kiroshi
from starbug.models.kubernetes.infrastructure.imagepullsecret import BinkCore
from starbug.models.kubernetes.infrastructure.postgres import Postgres
from starbug.models.kubernetes.infrastructure.rabbitmq import RabbitMQ
from starbug.models.kubernetes.infrastructure.redis import Redis


class SetupAIT:
    """Main logic for Creating, Managing and Destroying AIT Tests."""

    def __init__(self, test_id: str) -> None:
        """Initialize the AIT class."""
        self.test_id = test_id
        self.namespace_prefix = "ait"
        self.namespace_name = f"{self.namespace_prefix}-{self.test_id}"
        self.namespace = Namespace({
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
                "name": self.namespace_name,
            },
        })
        self.infrastructure_map = {
            "postgres": Postgres,
            "redis": Redis,
            "rabbitmq": RabbitMQ,
        }
        self.application_map = {
            "kiroshi": Kiroshi,
        }

    def _update_db_status(self, msg: str) -> None:
        with Session(engine) as session:
            session.execute(update(Tests).where(Tests.id == self.test_id).values(status=msg))
            session.commit()

    def _deploy_objects(self, objects: list) -> None:
        for obj in objects:
            logger.info(f"Deploying {obj.kind}/{obj.name}")
            self._update_db_status(f"Deploying {obj.kind}/{obj.name}")
            obj.create()

    def _wait_for_objects(self, objects: list) -> None:
        for obj in objects:
            if obj.kind == "Deployment":
                while True:
                    if obj.ready():
                        break
                    logger.info(f"waiting for {obj.kind}/{obj.name} to be ready")
                    sleep(0.25)

    def get_spec(self) -> dict | None:
        """Get the Spec for a AIT Test."""
        with Session(engine) as session:
            query = select(Tests).where(Tests.id == self.test_id)
            try:
                spec = session.execute(query).scalars().first().spec
            except AttributeError:
                return(None)
            return(spec)

    def deploy_infrastructure(self) -> None:
        """Deploy Infrastructure for a AIT Test."""
        spec = self.get_spec()["infrastructure"]
        components = []
        for application in spec:
            app = self.infrastructure_map[application["name"]]
            components.extend(app(namespace=self.namespace_name, image=application["image"]).obj())
        self._deploy_objects(components)
        self._wait_for_objects(components)

    def deploy_applications(self) -> None:
        """Deploy the Applications for a AIT Test."""
        spec = self.get_spec()["applications"]
        components = []
        for application in spec:
            app = self.application_map[application["name"]]
            components.extend(app(namespace=self.namespace_name, image=application["image"]).obj())
        self._deploy_objects(components)
        self._wait_for_objects(components)

    def destroy_test(self) -> None:
        """Destroy an existing AIT Test."""
        self.namespace.delete()

    def run(self) -> None:
        """Run an AIT Test."""
        namespace = self.namespace
        imagepullsecret = BinkCore(namespace=self.namespace_name).secret
        self._deploy_objects([namespace, imagepullsecret])
        self.deploy_infrastructure()
        self.deploy_applications()
        sleep(120)
        self.destroy_test()
        self._update_db_status("Complete")
