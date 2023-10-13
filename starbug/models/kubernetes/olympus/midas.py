"""Defines a Midas Instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value
from starbug.models.kubernetes import wait_for_migration
from starbug.models.kubernetes.infrastructure.postgres import wait_for_postgres
from starbug.models.kubernetes.infrastructure.rabbitmq import wait_for_rabbitmq
from starbug.models.kubernetes.infrastructure.redis import wait_for_redis


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
            "POSTGRES_DSN": "postgresql://postgres@postgres:5432/midas",
            "VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "AMQP_DSN": "amqp://rabbitmq:5672/",
            "REDIS_URL": "redis://redis:6379/0",
            "C_FORCE_ROOT": "True", # Remove once https://github.com/binkhq/python/blob/master/Dockerfile#L43 has propigated
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "annotations": {
                    "azure.workload.identity/client-id": get_secret_value("azure-identities", "midas_client_id"),
                },
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.rolebinding = RoleBinding({
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
                        "initContainers": [wait_for_postgres(), wait_for_rabbitmq(), wait_for_redis()],
                        "containers": [{
                            "name": self.name,
                            "image": self.image,
                            "command": ["linkerd-await", "--shutdown", "--"],
                            "args": [
                                "sh",
                                "-c",
                                "until alembic upgrade head; do echo 'Retrying'; sleep 2; done;",
                            ],
                            "env": [{"name": k, "value": v} for k, v in self.env.items()],
                            "securityContext": {
                                "runAsGroup": 10000,
                                "runAsUser": 10000,
                            },
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
                        "initContainers": [
                            wait_for_postgres(),
                            wait_for_rabbitmq(),
                            wait_for_redis(),
                            wait_for_migration(name="midas"),
                        ],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                            {
                                "name": "beat",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["celery", "-A", "app.api.celery", "beat", "--schedule", "/tmp/beat", "--pidfile", "/tmp/beat.pid"],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                            {
                                "name": "celery",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["celery", "-A", "app.api.celery", "worker", "--without-gossip", "--without-mingle", "--loglevel=info", "--pool=solo"],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                            {
                                "name": "consumer",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "consumer.py"],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                            {
                                "name": "worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "retry_worker.py"],
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
                            },
                            {
                                "name": "pushgateway",
                                "image": "prom/pushgateway:v1.6.2",
                                "imagePullPolicy": "IfNotPresent",
                                "args": [ "--web.listen-address=0.0.0.0:9100" ],
                                "ports": [{
                                    "name": "metrics",
                                    "containerPort": 9100,
                                }],
                            },
                        ],
                    },
                },
            },
        })

    def complete(self) -> tuple[ServiceAccount, RoleBinding, Service, Job, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.migrator, self.deployment)
