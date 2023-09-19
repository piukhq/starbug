import kr8s
from kr8s.objects import Namespace
from sqlalchemy import select
from sqlalchemy.orm import Session

from starbug.models.database import Tests, engine
from starbug.models.kubernetes.infrastructure.postgres import Postgres
from starbug.models.kubernetes.infrastructure.redis import Redis
from starbug.models.kubernetes.infrastructure.rabbitmq import RabbitMQ






class SetupAIT:
    """Main logic for Creating, Managing and Destroying AIT Tests."""

    def __init__(self, test_id: str) -> None:
        """Initialize the AIT class."""
        self.test_id = test_id
        self.namespace_prefix = "ait"
        self.namespace_name = f"{self.namespace_prefix}-{self.test_id}"

    def create_namespace(self) -> None:
        """Create a new Kubernetes Namespace."""
        namespace = Namespace({
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
                "name": self.namespace_name,
            },
        })
        namespace.create()

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
        infrastructure_map = {
            "postgres": Postgres,
            "redis": Redis,
            "rabbitmq": RabbitMQ,
        }
        spec = self.get_spec()["infrastructure"]
        for component in spec:
            resource = infrastructure_map[component["name"]]
            resource(namespace=self.namespace_name, image=component["image"])
            for r in resource:
                print(r)


    def deploy_applications(self) -> None:
        """Deploy the Applications for a AIT Test."""
        pass

    def destroy_test(self) -> None:
        """Destroy an existing AIT Test."""
        kr8s.get("namespaces", self.namespace)[0].delete()
