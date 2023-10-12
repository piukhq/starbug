"""Defines a Hermes Instance."""

from kr8s.objects import Deployment, Job, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value


class Hermes:
    """Defines a Hermes Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Hermes class."""
        self.namespace = namespace
        self.name = "hermes"
        self.image = image or "binkcore.azurecr.io/hermes:prod"
        self.labels = {"app": "hermes"}
        self.env = {
            "ATLAS_URL": "http://atlas/audit",
            "DEFAULT_API_VERSION": "1.1",
            "ENVIRONMENT_COLOR": "#FF69B4",
            "ENVIRONMENT_NAME": "Automated Integration Testing Envrionment",
            "HADES_URL": "http://hades",
            "HERMES_BLOB_STORAGE_CONTAINER": f"{namespace}-hermes-media",
            "HERMES_CUSTOM_DOMAIN": "https://api.gb.bink.com/",
            "HERMES_DEBUG": "False",
            "HERMES_SENTRY_DSN": "https://40ec46dd6a8940c4882501427e3e3a66@o503751.ingest.sentry.io/5589266",
            "HERMES_SENTRY_ENV": "ait",
            "METIS_URL": "http://metis",
            "MIDAS_URL": "http://midas",
            "NO_AZURE_STORAGE": "False",
            "SECURE_COOKIES": "True",
            "SPREEDLY_BASE_URL": "http://pelops/spreedly",
            "HERMES_BLOB_STORAGE_DSN": get_secret_value("azure-storage", "blob_connection_string_primary"),
            "HERMES_DATABASE_URL": "postgresql://postgres@postgres:5432/hermes",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "RABBIT_DSN": "amqp://guest:guest@rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "annotations": {
                    "azure.workload.identity/client-id": get_secret_value("azure-identities", "hermes_client_id"),
                },
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
                        "labels": self.labels | {"azure.workload.identity/use": "true"},
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
                        "restartPolicy": "Never",
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
                                "args": ["python", "manage.py", "migrate"],
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
                        "labels": self.labels | {"azure.workload.identity/use": "true"},
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "api",
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
                                "name": "api",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "image": self.image,
                                "command": ["/app/entrypoint.sh"],
                                "args": [
                                    "gunicorn",
                                    "--workers=2",
                                    "--error-logfile=-",
                                    "--access-logfile=-",
                                    "--bind=0.0.0.0:9000",
                                    "hermes.wsgi",
                                ],
                                "ports": [{"containerPort": 9000}],
                            },
                            {
                                "name": "celery",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "celery",
                                    "-A",
                                    "hermes",
                                    "worker",
                                    "--without-gossip",
                                    "--without-mingle",
                                    "--loglevel=info",
                                    "--pool=prefork",
                                    "--concurrency=2",
                                    "--queues=ubiquity-async-midas,record-history",
                                    "--events",
                                ],
                            },
                            {
                                "name": "beat",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "celery",
                                    "-A",
                                    "hermes",
                                    "beat",
                                    "--schedule",
                                    "/tmp/beat",
                                    "--pidfile",
                                    "/tmp/beat.pid",
                                ],
                            },
                            {
                                "name": "logic",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "python",
                                    "api_messaging/run.py",
                                ],
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

    def complete(self) -> tuple[ServiceAccount, Service, Job, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.migrator, self.deployment)
