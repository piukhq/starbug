"""Defines a Boreas Instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_pod


class Boreas:
    """Defines a Boreas Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Boreas class."""
        self.namespace = namespace
        self.name = "boreas"
        self.image = image or "binkcore.azurecr.io/boreas:prod"
        self.labels = {"app": "boreas"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "DEBUG": "False",
            "RABBITMQ_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "KEYVAULT_URL": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "boreas_client_id"),
                    },
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
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("rabbitmq")],
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
