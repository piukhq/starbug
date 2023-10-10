"""Defines a Asteria Instance."""

from kr8s.objects import Deployment


class Asteria:
    """Defines a Asteria Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Asteria class."""
        self.namespace = namespace
        self.name = "asteria"
        self.image = image or "binkcore.azurecr.io/asteria:prod"
        self.labels = {"app": "asteria"}
        self.env = {
            "POSTGRES_DSN": "postgres://postgres:5432/hermes",
        }
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
                            "kubectl.kubernetes.io/default-container": self.name,
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
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple[Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.deployment)
