"""Defines a Callbacca Instance."""

from kr8s.objects import Deployment, RoleBinding, ServiceAccount

from starbug.kubernetes import wait_for_pod


class Callbacca:
    """Defines a Callbacca Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Callbacca class."""
        self.namespace = namespace
        self.name = "callbacca"
        self.image = image or "binkcore.azurecr.io/callbacca:latest"
        self.labels = {"app": "callbacca"}
        self.env = {
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
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("redis")],
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
            },
        )

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.deployment)
