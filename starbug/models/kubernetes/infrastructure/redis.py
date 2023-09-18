"""Initialize the Redis class."""
from kr8s.objects import Deployment, Service, ServiceAccount


class Redis:
    """Define a Redis Instance."""

    def __init__(self, namespace: str) -> None:
        """Initialize the Redis class."""
        self.namespace = namespace
        self.name = "redis"
        self.image = "docker.io/redis:6"
        self.labels = {"app": "redis"}
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
                "ports": [{"port": 6379, "targetPort": 6379}],
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
                            },
                        ],
                    },
                },
            },
        })
