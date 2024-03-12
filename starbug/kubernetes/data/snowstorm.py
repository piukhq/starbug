"""Defines a Snowstorm Instance."""

from kr8s.objects import Deployment, Job, ServiceAccount

from starbug.kubernetes import wait_for_migration, wait_for_pod


class Snowstorm:
    """Defines a Snowstorm Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Snowstorm class."""
        self.namespace = namespace
        self.name = "snowstorm"
        self.image = image or "binkcore.azurecr.io/snowstorm:prod"
        self.labels = {"app": "snowstorm"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "DATABASE_DSN": "postgresql://postgres@postgres:5432/snowstorm",
            "REDIS_DSN": "redis://redis:6379/0",
            "RABBITMQ_DSN": "amqp://rabbitmq:5672/",
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
                            "labels": self.labels,
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                            ],
                            "containers": [
                                {
                                    "name": "migrator",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "args": ["alembic", "upgrade", "head"],
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
                            "serviceAccountName": self.name,
                            "initContainers": [wait_for_migration("snowstorm")],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                },
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, Job, Deployment]:
        """Iterate over the Snowstorm Instance."""
        return (self.serviceaccount, self.migrator, self.deployment)
