"""Defines a Skiron Instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import wait_for_pod


class Skiron:
    """Defines a Skiron Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Skiron class."""
        self.namespace = namespace
        self.name = "skiron"
        self.image = image or "binkcore.azurecr.io/skiron:latest"
        self.labels = {"app": "skiron"}
        self.env = {
            "AMQP_DSN": "amqp://rabbitmq:5672/",
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
                            "initContainers": [wait_for_pod("rabbitmq")],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
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
