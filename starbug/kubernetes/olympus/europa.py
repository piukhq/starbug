"""Defines a Europa Instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_migration, wait_for_pod


class Europa:
    """Defines a Europa Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Europa class."""
        self.namespace = namespace
        self.name = "europa"
        self.image = image or "binkcore.azurecr.io/europa:prod"
        self.labels = {"app": "europa"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "ENVIRONMENT_ID": "ait",
            "SENTRY_DSN": "https://63978f8a2fc04916bb67ea5e5e2f20ef@o503751.ingest.sentry.io/5778752",
            "TEAMS_WEBHOOK": "https://hellobink.webhook.office.com/webhookb2/bf220ac8-d509-474f-a568-148982784d19@a6e2367a-92ea-4e5a-b565-723830bcc095/IncomingWebhook/097759f226dd4be69a9f8a53d69a2e4f/ff7b6241-3a2d-471f-aa0c-cfefd7ce3a8f",
            "EUROPA_DATABASE_URI": "postgresql://postgres@postgres:5432/europa",
            "KEYVAULT_URI": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "europa_client_id"),
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
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"azure.workload.identity/use": "true"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "restartPolicy": "Never",
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("postgres")],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "args": ["python", "manage.py", "migrate"],
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
                            "labels": self.labels | {"azure.workload.identity/use": "true"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_pod("postgres"), wait_for_migration("europa")],
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

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Service, Job, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.migrator, self.deployment)
