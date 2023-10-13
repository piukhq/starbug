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
        })

    def complete(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.deployment)

def wait_for_redis() -> dict:
    """Return a wait-for init container."""
    return {
        "name": "wait-for-redis",
        "image": "ghcr.io/groundnuty/k8s-wait-for:v2.0",
        "imagePullPolicy": "Always",
        "args": ["pod", "-lapp=redis"],
    }
