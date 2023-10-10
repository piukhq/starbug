"""Defines a Midas Instance."""

from kr8s.objects import Deployment, Job, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value


class Midas:
    """Defines a Midas Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Midas class."""
        self.namespace = namespace
        self.name = "midas"
        self.image = image or "binkcore.azurecr.io/midas:prod"
        self.labels = {"app": "midas"}
        self.env = {
            "ATLAS_URL": "http://atlas",
            "AZURE_AAD_TENANT_ID": "a6e2367a-92ea-4e5a-b565-723830bcc095",
            "CONFIG_SERVICE_URL": "http://europa/config-service",
            "DEBUG": "False",
            "HADES_URL": "http://hades",
            "HERMES_URL": "http://hermes",
            "ITSU_VOUCHER_OFFER_ID": "23",
            "NEW_ICELAND_AGENT_ACTIVE": "True",
            "SENTRY_DSN": "https://846029dbfccb4f55ada16a7574dcc20b@o503751.ingest.sentry.io/5610025",
            "SENTRY_ENV": "ait",
            "POSTGRES_DSN": "postgres://postgres:5432/midas",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "AMQP_DSN": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "annotations": {
                "azure.workload.identity/client-id": get_secret_value("azure-identities", "midas_client_id"),
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
                        "containers": [{
                            "name": "migrator",
                            "image": self.image,
                            "command": ["linkerd-await", "--shutdown", "--"],
                            "args": ["alembic", "upgrade", "head"],
                            "env": [{"name": k, "value": v} for k, v in self.env.items()],
                        }],
                        "restartPolicy": "Never",
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
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
                        "labels": self.labels | {"azure.workload.identity/use": "true"},
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "midas",
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
                                "name": "midas",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                            },
                            {
                                "name": "beat",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["celery", "-A", "app.api.celery", "beat", "--schedule", "/tmp/beat", "--pidfile", "/tmp/beat.pid"],
                            },
                            {
                                "name": "celery",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["celery", "-A", "app.api.celery", "worker", "--without-gossip", "--without-mingle", "--loglevel=info", "--pool=solo"],
                            },
                            {
                                "name": "consumer",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "consumer.py"],
                            },
                            {
                                "name": "worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "retry_worker.py"],
                            },
                            {
                                "name": "pushgateway",
                                "image": "prom/pushgateway:v1.6.2",
                                "imagePullPolicy": "IfNotPresent",
                                "args": [ "--web.listen-address=0.0.0.0:9100" ],
                                "ports": [
                                    {
                                        "name": "metrics",
                                        "containerPort": 9100,
                                    },
                                ],
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple(ServiceAccount, Service, Job, Deployment):
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.migrator, self.deployment)
