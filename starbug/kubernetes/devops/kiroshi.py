"""Define a Kiroshi Instance."""
from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_migration, wait_for_pod


class Kiroshi:
    """Define a Kiroshi Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """.Initialize the Kiroshi class."""
        self.namespace = namespace
        self.name = "kiroshi"
        self.image = image or "binkcore.azurecr.io/kiroshi:prod"
        self.labels = {"app": "kiroshi"}
        self.env = {
            "BLOB_STORAGE_ACCOUNT_DSN": get_secret_value("azure-storage", "blob_connection_string_primary"),
            "DATABASE_DSN": "postgresql://postgres@postgres:5432/postgres",
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
        self.migrator = Job(
            {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {
                    "name": self.name + "-migrator",
                    "namespace": self.namespace,
                    "labels": self.labels,
                },
                "spec": {
                    "backoffLimit": 10,
                    "selector": self.labels,
                    "template": {
                        "metadata": {
                            "labels": self.labels,
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "restartPolicy": "Never",
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("postgres")],
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
                            "containers": [
                                {
                                    "name": self.name,
                                    "command": ["linkerd-await", "--shutdown", "--"],
                                    "args": ["alembic", "upgrade", "head"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "image": self.image,
                                },
                            ],
                        },
                    },
                },
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
                    "ports": [{"port": 80, "targetPort": 6502}],
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
                                "kubectl.kubernetes.io/default-container": "app",
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
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_migration(self.name)],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "args": ["kiroshi", "server", "image"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "ports": [{"name": "http", "containerPort": 6502, "protocol": "TCP"}],
                                },
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[Job, ServiceAccount, RoleBinding, Service, Deployment]:
        """Iterate over the Kiroshi Instance."""
        return (self.serviceaccount, self.rolebinding, self.migrator, self.service, self.deployment)
