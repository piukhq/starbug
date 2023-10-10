"""Defines a Harmonia instance."""

from kr8s.objects import Deployment, Job, ServiceAccount

from starbug.logic.secrets import get_secret_value
from starbug.models.kubernetes.custom_resources import SecretProviderClass


class Harmonia:
    """Defines a Harmonia instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Harmonia class."""
        self.namespace = namespace
        self.name = "harmonia"
        self.image = image or "binkcore.azurecr.io/harmonia:prod"
        self.labels = {"app": "harmonia"}
        self.env = {
            "TXM_POSTGRES_URI": "postgres://postgres:5432/harmonia",
            "TXM_REDIS_URL": "redis://redis:6379/0",
            "TXM_AMQP_DSN": "amqp://rabbitmq:5672/",
            "TXM_VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "TXM_BLOB_STORAGE_DSN": get_secret_value("azure-storage", "blob_connection_string_primary"),
            "TXM_BLOB_IMPORT_CONTAINER": f"{self.namespace}-harmonia-imports",
            "TXM_BLOB_EXPORT_CONTAINER": f"{self.namespace}-harmonia-exports",
            "TXM_BLOB_ARCHIVE_CONTAINER": f"{self.namespace}-harmonia-archives",
            "TXM_BLOB_AUDIT_CONTAINER": f"{self.namespace}-harmonia-atlas",
            "TXM_DEBUG": "False",
            "TXM_LOG_LEVEL": "info",
            "TXM_HERMES_URL": "http://hermes",
            "TXM_EUROPA_URL": "http://europa/config_service",
            "TXM_ATLAS_URL": "http://atlas/audit",
            "TXM_HERMES_SLUGS_TO_FORMAT": "whsmith-rewards",
            "TXM_HERMES_SLUG_FORMAT_STRING": "{}-mock",
            "TXM_MASTERCARD_TGX2_ENABLED": "true",
            "TXM_SENTRY_DSN": "https://39134637f8aa4bd190c23db0b23f6413@o503751.ingest.sentry.io/5609964",
            "TXM_SENTRY_ENV": "ait",
        }
        self.secretproviderclass = SecretProviderClass({
            "apiVersion": "secrets-store.csi.x-k8s.io/v1",
            "kind": "SecretProviderClass",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
            "spec": {
                "provider": "azure",
                "parameters": {
                    "clientID": get_secret_value("azure-identities", "harmonia_client_id"),
                    "keyvaultName": get_secret_value("azure-keyvault", "keyvault_name"),
                    "tenantId": get_secret_value("azure-identities", "tenant_id"),
                    "usePodIdentity": "false",
                    "useVMManagedIdentity": "false",
                    "objects": """array:
                        - |
                            objectName: test
                            objectType: secret
                    """,
                },
            },
        })
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "annotations": {
                "azure.workload.identity/client-id": get_secret_value("azure-identities", "harmonia_client_id"),
            },
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
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
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--shutdown", "--"],
                                "args": ["alembic", "upgrade", "head"],
                            },
                        ],
                        "restartPolicy": "Never",
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
                        "containers": [
                            {
                                "name": "api",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": [
                                    "gunicorn",
                                    "-b",
                                    "0.0.0.0:9000",
                                    "--access-logfile",
                                    "-",
                                    "--error-logfile",
                                    "-",
                                    "app.api.app:app",
                                ],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "export-agent-iceland-bonus-card",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txexport", "--agent", "iceland-bonus-card", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "export-retry-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "export-retry"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "export-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "export"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "identify-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "identify"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-amex-auth",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "amex-auth", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-amex-settlement",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "amex-settlement", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-costa",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "costa", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-iceland-bonus-card",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "iceland-bonus-card", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-itsu",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "itsu", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-mastercard-auth",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "mastercard-auth", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_MASTERCARD_TGX2_ENABLED", "value": "true"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-mastercard-refund",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "mastercard-refund", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-mastercard-settled",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "mastercard-settled", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-slim-chickens",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "slim-chickens", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-stonegate",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "stonegate", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-visa-auth",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "visa-auth", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-visa-refund",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "visa-refund", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-agent-visa-settle",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["tximport", "--agent", "visa-settle", "--no-user-input", "--quiet"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "import-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "import"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "matching-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "matching"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "matching-worker-slow",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "matching_slow"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
                                ],
                            },
                            {
                                "name": "streaming-worker",
                                "image": self.image,
                                "imagePullPolicy": "Always",
                                "command": ["linkerd-await", "--"],
                                "args": ["txcore", "worker"],
                                "env": [{"name": k, "value": v} for k, v in self.env.items()] + [
                                    {"name": "TXM_RQ_QUEUES", "value": "streaming"},
                                ],
                                "volumeMounts": [
                                    {"name": "keyvault", "mountPath": "/mnt/secrets-store", "readOnly": True},
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
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "volumes": [
                            {
                                "name": "keyvault",
                                "csi": {
                                    "driver": "secrets-store.csi.k8s.io",
                                    "readOnly": True,
                                    "volumeAttributes": {
                                        "secretProviderClass": self.name,
                                    },
                                },
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple[ServiceAccount, Job, Deployment, SecretProviderClass]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.migrator, self.deployment, self.secretproviderclass)
