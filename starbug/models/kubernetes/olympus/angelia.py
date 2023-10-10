"""Defines a Angelia instance."""

from kr8s.objects import Deployment, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value


class Angelia:
    """Define an Angelia Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Angelia class."""
        self.namespace = namespace
        self.name = "angelia"
        self.image = image or "docker.io/angelia:prod"
        self.labels = {"app": "angelia"}
        self.env = {
            "CUSTOM_DOMAIN": "https://api.gb.bink.com/content/hermes",
            "PENDING_VOUCHERS_FLAG": "True",
            "POSTGRES_DSN" : "postgres://postgres:5432/hermes",
            "RABBIT_DSN": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "SENTRY_DSN": "https://71a82577c1844361a2c37e8a9e4c553b@o503751.ingest.sentry.io/5962550",
            "SENTRY_ENVIRONMENT": "ait",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "annotations": {
                "azure.workload.identity/client-id": get_secret_value("azure-identities", "angelia_client_id"),
            },
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
                        "labels": self.labels | {"azure.workload.identity/use": "true"},
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "angelia",
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
                                "name": "angelia",
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9080}],
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple[ServiceAccount, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.deployment)
