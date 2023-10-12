"""Defines a Boreas Instance."""

from kr8s.objects import Deployment, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value


class Boreas:
    """Defines a Boreas Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Boreas class."""
        self.namespace = namespace
        self.name = "boreas"
        self.image = image or "binkcore.azurecr.io/boreas:prod"
        self.labels = {"app": "boreas"}
        self.env = {
            "DEBUG": "False",
            "RABBITMQ_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "KEYVAULT_URL": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "annotations": {
                    "azure.workload.identity/client-id": get_secret_value("azure-identities", "boreas_client_id"),
                },
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

    def complete(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return self.serviceaccount, self.service, self.deployment
