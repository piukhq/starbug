"""Define the Angelia class."""
from kr8s.objects import Deployment, Service, ServiceAccount


class Angelia:
    """Define an Angelia Instance."""

    def __init__(self) -> None:
        """Initialize the Angelia class."""
        self.namespace = "angelia"
        self.name = "angelia"
        self.image = "docker.io/angelia:latest"
        self.labels = {"app": "angelia"}
        self.env = {
            "POSTGRES_DSN": "postgres://postgres:postgres@postgres:5432/angelia",
            "RABBIT_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
            "PENDING_VOUCHERS_FLAG": "True",
            "SENTRY_DSN": "https://71a82577c1844361a2c37e8a9e4c553b@o503751.ingest.sentry.io/5962550",
            "SENTRY_ENVIRONMENT": "AIT",
            "VAULT_URL": "https://uksouth-ait-4wk6.vault.azure.net/",
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
                            "kubectl.kubernetes.io/default-container": "angelia",
                        },
                    },
                    "spec": {
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "angelia",
                                "image": self.image,
                                "env": [
                                    {
                                        "name": "ANGELIA_PORT",
                                        "value": "8080",
                                    },
                                    {
                                        "name": "ANGELIA_NAMESPACE",
                                        "valueFrom": {
                                            "fieldRef": {
                                                "fieldPath": "metadata.namespace",
                                            },
                                        },
                                    },
                                ],
                                "ports": [{"containerPort": 8080}],
                            },
                        ],
                    },
                },
            },
        })
