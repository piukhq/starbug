"""Defines an Eos Instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value
from starbug.models.kubernetes import wait_for_migration
from starbug.models.kubernetes.infrastructure.postgres import wait_for_postgres
from starbug.models.kubernetes.infrastructure.redis import wait_for_redis


class Eos:
    """Defines an Eos Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Eos class."""
        self.namespace = namespace
        self.name = "eos"
        self.image = image or "binkcore.azurecr.io/eos:prod"
        self.labels = {"app": "eos"}
        self.env = {
            "OAUTH_CLIENT_ID": "bbcb94ca-d25f-4a77-949a-c4a7da6a19f0",
            "OAUTH_CLIENT_SECRET": "7~PF_wKl33M6Ed9w1.kW-stIzgbt~yP_It",
            "OAUTH_TENANT_ID": "a6e2367a-92ea-4e5a-b565-723830bcc095",
            "AMEX_API_HOST": "https://api.qa2s.americanexpress.com",
            "SENTRY_DSN": "https://dd0b42d40f3f49fdb413f6b4529741bd@o503751.ingest.sentry.io/5639775",
            "SENTRY_ENV": "ait",
            "EOS_DATABASE_URI": "postgresql://postgres@postgres:5432/eos",
            "REDIS_URL": "redis://redis:6379/0",
            "KEY_VAULT": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "annotations": {
                    "azure.workload.identity/client-id": get_secret_value("azure-identities", "eos_client_id"),
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
                        "restartPolicy": "Never",
                        "serviceAccountName": self.name,
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "initContainers": [wait_for_postgres(), wait_for_redis()],
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
                                "securityContext": {
                                    "runAsGroup": 10000,
                                    "runAsUser": 10000,
                                },
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
                        "initContainers": [wait_for_postgres(), wait_for_redis(), wait_for_migration(name="eos")],
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "command": ["linkerd-await", "--"],
                                "args": ["python", "manage.py", "worker"],
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
        })

    def complete(self) -> tuple[ServiceAccount, RoleBinding, Service, Job, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.migrator, self.deployment)
