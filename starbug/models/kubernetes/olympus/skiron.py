"""Defines a Skiron Instance."""

from kr8s.objects import Deployment, Service, ServiceAccount


class Skiron:
    """Defines a Skiron Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Skiron class."""
        self.namespace = namespace
        self.name = "skiron"
        self.image = image or "binkcore.azurecr.io/skiron:prod"
        self.labels = {"app": "skiron"}
        self.env = {
            "AMQP_DSN": "amqp://rabbitmq:5672/",
        }
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
                "ports": [{"port": 80, "targetPort": 9000}],
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
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "containers": [{
                            "name": self.name,
                            "image": self.image,
                            "imagePullPolicy": "Always",
                            "env": [{"name": k, "value": v} for k, v in self.env.items()],
                            "ports": [{"containerPort": 9000}],
                        }],
                    },
                },
            },
        })
