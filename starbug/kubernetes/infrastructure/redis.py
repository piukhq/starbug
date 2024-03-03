"""Initialize the Redis class."""

from kr8s.objects import Deployment, Service, ServiceAccount


class Redis:
    """Define a Redis Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Redis class."""
        self.namespace = namespace
        self.image = image or "docker.io/redis:6"
        self.name = "redis"
        self.labels = {"app": "redis"}
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                },
            },
        )
        self.service = Service(
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                    "labels": self.labels,
                },
                "spec": {
                    "ports": [{"port": 6379, "targetPort": 6379}],
                    "selector": self.labels,
                },
            },
        )
        self.deployment = Deployment(
            {
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
                                "kubectl.kubernetes.io/default-container": "redis",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "containers": [
                                {
                                    "name": "redis",
                                    "image": self.image,
                                    "ports": [{"containerPort": 6379}],
                                    "readinessProbe": {
                                        "exec": {
                                            "command": ["redis-cli", "ping"],
                                        },
                                        "initialDelaySeconds": 5,
                                        "periodSeconds": 10,
                                    },
                                },
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.deployment)
