import kr8s
from kr8s.objects import Namespace


class SetupAIT:
    """Main logic for Creating, Managing and Destroying AIT Tests."""

    def __init__(self, namespace: str) -> None:
        """Initialize the AIT class."""
        self.namespace = namespace

    def create_namespace(self) -> None:
        """Create a new Kubernetes Namespace."""
        namespace = Namespace({
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "annotations": {
                    "linkerd.io/inject": "enabled",
                },
                "name": self.namespace,
            },
        })
        namespace.create()

    def deploy_infrastructure(self) -> None:
        """Deploy Infrastructure for a AIT Test."""
        pass

    def deploy_applications(self) -> None:
        """Deploy the Applications for a AIT Test."""
        pass

    def destroy_test(self) -> None:
        """Destroy an existing AIT Test."""
        kr8s.get("namespaces", self.namespace)[0].delete()
