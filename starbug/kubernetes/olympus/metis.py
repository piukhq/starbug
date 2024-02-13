"""Defines a Metis Instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value


class Metis:
    """Defines a Metis Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Metis class."""
        self.namespace = namespace
        self.name = "metis"
        self.image = image or "binkcore.azurecr.io/metis:prod"
        self.labels = {"app": "metis"}
        self.env = {
            "DEBUG": "True",
            "HERMES_URL": "http://hermes",
            "METIS_PRE_PRODUCTION": "False",
            "METIS_TESTING": "False",
            "SENTRY_DSN": "https://9aeb0741cef34c4ebce7e560c56cac2c@o503751.ingest.sentry.io/5610024",
            "SENTRY_ENV": "ait",
            "SPREEDLY_BASE_URL": "http://pelops/spreedly",
            "STUBBED_VOP_URL": "http://pelops",
            "AZURE_VAULT_URL": get_secret_value("azure-keyvault", "url"),
            "AMQP_URL": "amqp://rabbitmq:5672/",
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "metis_client_id"),
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
        self.service = Service(
            {
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
                            "labels": self.labels | {"azure.workload.identity/use": "true"},
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": self.name,
                            },
                        },
                        "spec": {
                            "serviceAccountName": self.name,
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "ports": [{"containerPort": 9000}],
                                    "securityContext": {
                                        "runAsGroup": 10000,
                                        "runAsUser": 10000,
                                    },
                                },
                                {
                                    "name": "celery",
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "command": ["linkerd-await", "--"],
                                    "args": [
                                        "celery",
                                        "-A",
                                        "metis.tasks",
                                        "worker",
                                        "--without-gossip",
                                        "--without-mingle",
                                        "--loglevel=info",
                                        "--pool=solo",
                                    ],
                                    "securityContext": {
                                        "runAsGroup": 10000,
                                        "runAsUser": 10000,
                                    },
                                },
                                {
                                    "name": "pushgateway",
                                    "image": "prom/pushgateway:v1.6.2",
                                    "imagePullPolicy": "IfNotPresent",
                                    "args": ["--web.listen-address=0.0.0.0:9100"],
                                    "ports": [{"name": "metrics", "containerPort": 9100}],
                                },
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.deployment)
