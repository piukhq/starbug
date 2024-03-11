"""Defines a Atlas Instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import wait_for_migration, wait_for_pod


class Atlas:
    """Defines a Atlas Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Atlas class."""
        self.namespace = namespace
        self.name = "atlas"
        self.image = image or "binkcore.azurecr.io/atlas:prod"
        self.labels = {"app": "atlas"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "AMQP_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "ATLAS_DATABASE_URL": "postgresql://postgres@postgres:5432/atlas",
            "ATLAS_DEBUG": "True",
            "LOG_LEVEL": "INFO",
            "SENTRY_DSN": "https://593a9ed708df47fab1242f6eca0f544a@o503751.ingest.sentry.io/5609979",
            "SENTRY_ENV": "ait",
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
                            "labels": self.labels,
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "api",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_migration("atlas"),
                            ],
                            "containers": [
                                {
                                    "name": "api",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "ports": [{"containerPort": 9000}],
                                    "securityContext": {
                                        "runAsGroup": 10000,
                                        "runAsUser": 10000,
                                    },
                                },
                                {
                                    "name": "consumer",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "args": ["python", "manage.py", "consume"],
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
        return (self.serviceaccount, self.rolebinding, self.service, self.job, self.deployment)
