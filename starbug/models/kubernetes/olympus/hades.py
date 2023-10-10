"""Defines a Hades Instance."""

from kr8s.objects import Deployment, Job, Service, ServiceAccount


class Hades:
    """Defines a Hades Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Hades class."""
        self.namespace = namespace
        self.name = "hades"
        self.image = image or "binkcore.azurecr.io/hades:prod"
        self.labels = {"app": "hades"}
        self.env = {
            "HERMES_URL": "http://hermes",
            "SENTRY_DSN": "https://4904faba430f4d92b6dbaac432de0c7e@o503751.ingest.sentry.io/5610000",
            "SENTRY_ENV": "ait",
            "HADES_DATABASE_URL": "postgres://postgres:5432/hades",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.service = Service({
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
        })
        self.migrator = Job({
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
                        "nodeSelector": {
                            "kubernetes.azure.com/scalesetpriority": "spot",
                        },
                        "tolerations": [{
                            "key": "kubernetes.azure.com/scalesetpriority",
                            "operator": "Equal",
                            "value": "spot",
                            "effect": "NoSchedule",
                        }],
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [
                                    {"name": k, "value": v}
                                    for k, v in self.env.items()
                                ],
                                "command": ["linkerd-await", "--shutdown", "--"],
                                "args": ["alembic", "upgrade", "head"],
                            },
                        ],
                    },
                },
            },
        })
        self.deployment = Deployment({
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
                        "tolerations": [{
                            "key": "kubernetes.azure.com/scalesetpriority",
                            "operator": "Equal",
                            "value": "spot",
                            "effect": "NoSchedule",
                        }],
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple[ServiceAccount, Service, Job, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.migrator, self.deployment)
