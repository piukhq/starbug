"""Defines a Plutus Instance."""

from kr8s.objects import Deployment, ServiceAccount


class Plutus:
    """Defines a Plutus Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Plutus class."""
        self.namespace = namespace
        self.name = "plutus"
        self.image = image or "binkcore.azurecr.io/plutus:prod"
        self.labels = {"app": "plutus"}
        self.env = {
            "CONSUME_QUEUE": "tx_plutus_dw",
            "DEAD_LETTER_EXCHANGE": "tx_plutus_dl_exchange",
            "DEAD_LETTER_QUEUE": "tx_plutus_dl_queue",
            "DEBUG": "True",
            "DW_QUEUE": "tx_export_dw",
            "AMQP_URL": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
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
                            "kubectl.kubernetes.io/default-container": "consumer",
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
                        "containers": [
                            {
                                "name": "consumer",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "/app/app/message_consumer.py"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                            },
                            {
                                "name": "dlx",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "/app/app/dead_letter_consumer.py"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                            },
                        ],
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                    },
                },
            },
        })

    def complete(self) -> tuple[ServiceAccount, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.deployment)
