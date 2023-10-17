"""Defines a Pelops Instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import wait_for_pod


class Pelops:
    """Defines a Pelops Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Pelops class."""
        self.namespace = namespace
        self.name = "pelops"
        self.image = image or "binkcore.azurecr.io/pelops:latest"
        self.labels = {"app": "pelops"}
        self.env = {
            "PELOPS_DEBUG": "False",
            "REDIS_DSN": "redis://redis:6379/0",
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
                    "ports": [{"port": 80, "targetPort": 9000}],
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
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "nodeSelector": {
                                "kubernetes.azure.com/scalesetpriority": "spot",
                            },
                            "tolerations": [
                                {
                                    "key": "kubernetes.azure.com/scalesetpriority",
                                    "operator": "Equal",
                                    "value": "spot",
                                    "effect": "NoSchedule",
                                },
                            ],
                            "serviceAccountName": self.name,
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
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

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.deployment)
