"""Defines a Asteria Instance."""

from kr8s.objects import Deployment, RoleBinding, ServiceAccount

from starbug.models.kubernetes import wait_for_migration
from starbug.models.kubernetes.infrastructure.postgres import wait_for_postgres
from starbug.models.kubernetes.infrastructure.rabbitmq import wait_for_rabbitmq
from starbug.models.kubernetes.infrastructure.redis import wait_for_redis


class Asteria:
    """Defines a Asteria Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Asteria class."""
        self.namespace = namespace
        self.name = "asteria"
        self.image = image or "binkcore.azurecr.io/asteria:latest"
        self.labels = {"app": "asteria"}
        self.env = {
            "POSTGRES_DSN": "postgresql://postgres@postgres:5432/hermes",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.rolebinding = RoleBinding({
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
                        "initContainers": [
                            wait_for_postgres(),
                            wait_for_rabbitmq(),
                            wait_for_redis(),
                            wait_for_migration(name="hermes"),
                        ],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                        ],
                    },
                },
            },
        })

    def complete(self) -> tuple[ServiceAccount, RoleBinding, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.deployment)
