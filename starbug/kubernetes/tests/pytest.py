"""Provides a pytest based test suite."""

from kr8s.objects import Job, Role, RoleBinding, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_pod
from starbug.kubernetes.internal.scutter import scutter_container, scutter_role, scutter_rolebinding


class Pytest:
    """Provides a pytest based test suite."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Pytest Class."""
        self.name = "pytest"
        self.namespace = namespace
        self.image = image or "binkcore.azurecr.io/pyqa-apiv2:staging"
        self.env = {
            "BLOB_STORAGE_ACCOUNT_DSN": get_secret_value("azure-storage", "blob_connection_string_primary"),
            "HERMES_DATABASE_URI": "postgresql://postgres@postgres:5432/hermes",
            "HARMONIA_DATABASE_URI": "postgresql://postgres@postgres:5432/harmonia",
            "SNOWSTORM_DATABASE_URI": "postgresql://postgres@postgres:5432/snowstorm",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "pytest_client_id"),
                    },
                    "name": self.name,
                    "namespace": self.namespace,
                },
            },
        )
        self.scutter_role = scutter_role(namespace=self.namespace)
        self.scutter_rolebinding = scutter_rolebinding(namespace=self.namespace, service_account_name=self.name)
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
        self.test = Job(
            {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                    "labels": {
                        "app": self.name,
                    },
                },
                "spec": {
                    "template": {
                        "metadata": {
                            "name": self.name,
                            "labels": {
                                "app": self.name,
                            },
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("angelia")],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "args": [
                                        "pytest",
                                        "--html=/mnt/results/report.html",
                                        "--self-contained-html",
                                        "-m=bink_regression_api2",
                                        "--channel=bink",
                                        "--env=staging",
                                    ],
                                    "volumeMounts": [{"name": "results", "mountPath": "/mnt/results"}],
                                    "securityContext": {
                                        "runAsGroup": 0,
                                        "runAsUser": 0,
                                    },
                                },
                                scutter_container(filename="report.html"),
                            ],
                            "restartPolicy": "Never",
                            "volumes": [{"name": "results", "emptyDir": {"medium": "Memory"}}],
                        },
                    },
                    "backoffLimit": 0,
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, Role, RoleBinding, RoleBinding, Job]:
        """Deploy the Pytest Test Suite."""
        return (self.serviceaccount, self.scutter_role, self.scutter_rolebinding, self.rolebinding, self.test)
