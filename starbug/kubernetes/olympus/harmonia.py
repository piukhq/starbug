"""Defines a Harmonia instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_migration, wait_for_pod


class Harmonia:
    """Defines a Harmonia instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Harmonia class."""
        self.namespace = namespace
        self.name = "harmonia"
        self.image = image or "binkcore.azurecr.io/harmonia:prod"
        self.labels = {"app": "harmonia"}
        self.env = {
            "LINKERD_AWAIT_DISABLED": "true",
            "TXM_POSTGRES_URI": "postgresql://postgres@postgres:5432/harmonia",
            "TXM_REDIS_URL": "redis://redis:6379/0",
            "TXM_AMQP_DSN": "amqp://rabbitmq:5672/",
            "TXM_VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "TXM_BLOB_STORAGE_DSN": get_secret_value("azure-storage", "blob_connection_string_primary"),
            "TXM_BLOB_IMPORT_CONTAINER": f"{self.namespace}-harmonia-imports",
            "TXM_BLOB_EXPORT_CONTAINER": f"{self.namespace}-harmonia-exports",
            "TXM_BLOB_ARCHIVE_CONTAINER": f"{self.namespace}-harmonia-archives",
            "TXM_BLOB_AUDIT_CONTAINER": f"{self.namespace}-harmonia-atlas",
            "TXM_API_AUTH_ENABLED": "False",
            "TXM_DEBUG": "False",
            "TXM_LOG_LEVEL": "info",
            "TXM_HERMES_URL": "http://hermes-api",
            "TXM_EUROPA_URL": "http://europa-api/config_service",
            "TXM_ATLAS_URL": "http://atlas-api/audit",
            "TXM_HERMES_SLUGS_TO_FORMAT": "whsmith-rewards",
            "TXM_HERMES_SLUG_FORMAT_STRING": "{}-mock",
            "TXM_MASTERCARD_TGX2_ENABLED": "true",
            "TXM_SENTRY_DSN": "https://39134637f8aa4bd190c23db0b23f6413@o503751.ingest.sentry.io/5609964",
            "TXM_SENTRY_ENV": "ait",
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "harmonia_client_id"),
                    },
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
                            "serviceAccountName": self.name,
                            "restartPolicy": "Never",
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                            ],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "args": ["alembic", "upgrade", "head"],
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
        self.api_service = Service(
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": self.name + "-api",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "api"},
                },
                "spec": {
                    "ports": [{"port": 80, "targetPort": 9000}],
                    "selector": self.labels | {"component": "api"},
                },
            },
        )
        self.api = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-api",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "api"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "api"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "api"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
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
            },
        )
        self.export_retry_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-export-retry-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "export-retry-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "export-retry-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "export-retry-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "export-retry"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.export_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-export-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "export-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "export-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "export-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [{"name": "TXM_RQ_QUEUES", "value": "export"}],
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
        self.identify_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-identify-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "identify-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "identify-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "identify-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [{"name": "TXM_RQ_QUEUES", "value": "identify"}],
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
        self.import_agent_amex_auth = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-amex-auth",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-amex-auth"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-amex-auth"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-amex-auth"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "amex-auth", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_amex_settlement = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-amex-settlement",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-amex-settlement"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-amex-settlement"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-amex-settlement"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "amex-settlement", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_costa = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-costa",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-costa"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-costa"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-costa"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "costa", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_itsu = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-itsu",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-itsu"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-itsu"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-itsu"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "itsu", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_mastercard_auth = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-mastercard-auth",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-mastercard-auth"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-mastercard-auth"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-mastercard-auth"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "mastercard-auth", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [
                                        {"name": "TXM_MASTERCARD_TGX2_ENABLED", "value": "true"},
                                    ],
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
        self.import_agent_mastercard_refund = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-mastercard-refund",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-mastercard-refund"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-mastercard-refund"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-mastercard-refund"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "mastercard-refund", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_slim_chickens = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-slim-chickens",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-slim-chickens"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-slim-chickens"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-slim-chickens"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "slim-chickens", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_stonegate = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-stonegate",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-stonegate"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-stonegate"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-stonegate"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "stonegate", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_visa_auth = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-visa-auth",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-visa-auth"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-visa-auth"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-visa-auth"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "visa-auth", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_visa_refund = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-visa-refund",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-visa-refund"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-visa-refund"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-visa-refund"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "app",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "visa-refund", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_agent_visa_settlement = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-agent-visa-settlement",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-agent-visa-settlement"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-agent-visa-settlement"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-agent-visa-settlement"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "import-agent-visa-settlement",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["tximport", "--agent", "visa-settlement", "--no-user-input", "--quiet"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
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
        self.import_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-import-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "import-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "import-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "import-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "import-worker",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [
                                        {"name": "TXM_RQ_QUEUES", "value": "import"},
                                    ],
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
        self.matching_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-matching-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "matching-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "matching-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "matching-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "matching-worker",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [
                                        {"name": "TXM_RQ_QUEUES", "value": "matching"},
                                    ],
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
        self.matching_worker_slow = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-matching-worker-slow",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "matching-worker-slow"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "matching-worker-slow"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "matching-worker-slow"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "matching-worker-slow",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [
                                        {"name": "TXM_RQ_QUEUES", "value": "matching_slow"},
                                    ],
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
        self.streaming_worker = Deployment(
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": self.name + "-streaming-worker",
                    "namespace": self.namespace,
                    "labels": self.labels | {"component": "streaming-worker"},
                },
                "spec": {
                    "replicas": 1,
                    "selector": {
                        "matchLabels": self.labels | {"component": "streaming-worker"},
                    },
                    "template": {
                        "metadata": {
                            "labels": self.labels | {"component": "streaming-worker"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "app",
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "initContainers": [
                                wait_for_pod("postgres"),
                                wait_for_pod("rabbitmq"),
                                wait_for_pod("redis"),
                                wait_for_migration("harmonia"),
                            ],
                            "containers": [
                                {
                                    "name": "streaming-worker",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "args": ["txcore", "worker"],
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()]
                                    + [
                                        {"name": "TXM_RQ_QUEUES", "value": "streaming"},
                                    ],
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

    def deploy(
        self,
    ) -> tuple[
        ServiceAccount,
        RoleBinding,
        Job,
        Service,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
        Deployment,
    ]:
        """Return all deployable objects as a tuple."""
        return (
            self.serviceaccount,
            self.rolebinding,
            self.migrator,
            self.api_service,
            self.api,
            self.export_retry_worker,
            self.export_worker,
            self.identify_worker,
            self.import_agent_amex_auth,
            self.import_agent_amex_settlement,
            self.import_agent_costa,
            self.import_agent_itsu,
            self.import_agent_mastercard_auth,
            self.import_agent_mastercard_refund,
            self.import_agent_slim_chickens,
            self.import_agent_stonegate,
            self.import_agent_visa_auth,
            self.import_agent_visa_refund,
            self.import_agent_visa_settlement,
            self.import_worker,
            self.matching_worker,
            self.matching_worker_slow,
            self.streaming_worker,
        )
