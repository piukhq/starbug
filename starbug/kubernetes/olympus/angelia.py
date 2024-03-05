"""Defines a Angelia instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_migration, wait_for_pod


class Angelia:
    """Define an Angelia Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Angelia class."""
        self.namespace = namespace
        self.name = "angelia"
        self.image = image or "binkcore.azurecr.io/angelia:prod"
        self.labels = {"app": "angelia"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "CUSTOM_DOMAIN": "https://api.gb.bink.com/content/hermes",
            "PENDING_VOUCHERS_FLAG": "True",
            "POSTGRES_DSN": "postgresql://postgres@postgres:5432/hermes",
            "RABBIT_DSN": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "SENTRY_DSN": "https://71a82577c1844361a2c37e8a9e4c553b@o503751.ingest.sentry.io/5962550",
            "SENTRY_ENVIRONMENT": "ait",
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "angelia_client_id"),
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
                    "name": self.name + "-api",
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
                            "labels": self.labels | {"azure.workload.identity/use": "true"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "angelia",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("hermes"),
                            ],
                            "containers": [
                                {
                                    "name": "angelia",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "ports": [{"containerPort": 9080}],
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
