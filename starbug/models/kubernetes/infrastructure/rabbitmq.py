"""Define a RabbitMQ Instance."""
from kr8s.objects import Deployment, Service, ServiceAccount


class RabbitMQ:
    """Define a RabbitMQ Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the RabbitMQ class."""
        self.namespace = namespace
        self.name = "rabbitmq"
        self.image = "docker.io/rabbitmq:3"
        self.labels = {"app": "rabbitmq"}
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.service = Service({
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
            },
            "spec": {
                "ports": [{"port": 5672, "targetPort": 5672}],
                "selector": self.labels,
            },
        })
        self.deployment = Deployment({
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": self.labels,
                },
                "template": {
                    "metadata": {
                        "labels": self.labels,
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "rabbitmq",
                        },
                    },
                    "spec": {
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "rabbitmq",
                                "image": self.image,
                                "ports": [{"containerPort": 5672}],
                            },
                        ],
                    },
                },
            },
        })

    def __iter__(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Iterate over the Kiroshi Instance."""
        yield from (self.serviceaccount, self.service, self.deployment)
