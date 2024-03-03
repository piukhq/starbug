"""Defines a Plutus Instance."""

from kr8s.objects import Deployment, RoleBinding, ServiceAccount

from starbug.kubernetes import wait_for_pod


class Plutus:
    """Defines a Plutus Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Plutus class."""
        self.namespace = namespace
        self.name = "plutus"
        self.image = image or "binkcore.azurecr.io/plutus:prod"
        self.labels = {"app": "plutus"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "CONSUME_QUEUE": "tx_plutus_dw",
            "DEAD_LETTER_EXCHANGE": "tx_plutus_dl_exchange",
            "DEAD_LETTER_QUEUE": "tx_plutus_dl_queue",
            "DEBUG": "True",
            "DW_QUEUE": "tx_export_dw",
            "AMQP_URL": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
        }
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
        self.rolebinding = RoleBinding(
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "RoleBinding",
                "metadata": {
                    "name": self.name + "-k8s-wait-for",
                    "namespace": self.namespace,
                },
                "roleRef": {
                    "apiGroup": "rbac.authorization.k8s.io",
                    "kind": "Role",
                    "name": "k8s-wait-for",
                },
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": self.name,
                        "namespace": self.namespace,
                    },
                ],
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
                                "kubectl.kubernetes.io/default-container": "consumer",
                            },
                        },
                        "spec": {
                            "initContainers": [wait_for_pod("rabbitmq"), wait_for_pod("redis")],
                            "containers": [
                                {
                                    "name": "consumer",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["python", "/app/app/message_consumer.py"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "securityContext": {
                                        "runAsGroup": 10000,
                                        "runAsUser": 10000,
                                    },
                                },
                                {
                                    "name": "dlx",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["python", "/app/app/dead_letter_consumer.py"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "securityContext": {
                                        "runAsGroup": 10000,
                                        "runAsUser": 10000,
                                    },
                                },
                            ],
                            "serviceAccountName": self.name,
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.deployment)
