"""Define a Postgres Instance."""
from kr8s.objects import Deployment, Service, ServiceAccount


class Postgres:
    """Define a Postgres Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """.Initialize the Postgres class."""
        self.namespace = namespace
        self.image = image or "docker.io/postgres:15"
        self.name = "postgres"
        self.labels = {"app": "postgres"}
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
                "ports": [{"port": 5432, "targetPort": 5432}],
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
                            "kubectl.kubernetes.io/default-container": "postgres",
                        },
                    },
                    "spec": {
                        "nodeSelector": {
                            "kubernetes.azure.com/scalesetpriority": "spot",
                        },
                        "tolerations": [{
                            "key": "kubernetes.azure.com/scalesetpriority",
                            "operator": "Equal",
                            "value": "spot",
                            "effect": "NoSchedule",
                        }],
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "postgres",
                                "image": self.image,
                                "ports": [{"containerPort": 5432}],
                                "env": [
                                    {
                                        "name": "POSTGRES_HOST_AUTH_METHOD",
                                        "value": "trust",
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
        })

    def obj(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Loop over the Kiroshi Instance."""
        return (self.serviceaccount, self.service, self.deployment)
