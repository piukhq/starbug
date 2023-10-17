"""Defines a Zephyrus Instance."""

from kr8s.objects import Deployment, RoleBinding, Service, ServiceAccount

from starbug.kubernetes import get_secret_value, wait_for_pod


class Zephyrus:
    """Defines a Zephyrus Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Zephyrus class."""
        self.namespace = namespace
        self.name = "zephyrus"
        self.image = image or "binkcore.azurecr.io/zephyrus:prod"
        self.labels = {"app": "zephyrus"}
        self.env = {
            "AZURE_CERTIFICATE_FOLDER": "certs",
            "AZURE_CONTAINER": "dev-zephyrus",
            "HERMES_URL": "http://hermes",
            "MASTERCARD_CERTIFICATE_BLOB_NAME": "certificate.pem",
            "SENTRY_DSN": "https://286fc47f67974edc9761b7ae7fc502c2@o503751.ingest.sentry.io/5610043",
            "SENTRY_ENV": "ait",
            "VISA_PASSWORD": "7Taq_e-VY9KU",
            "VISA_USERNAME": "VisaTxTest@testbink.com",
            "KEYVAULT_URI": get_secret_value("azure-keyvault", "url"),
            "AMQP_URL": "amqp://rabbitmq:5672/",
        }
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "zephyrus_client_id"),
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
                            "tolerations": [
                                {
                                    "key": "kubernetes.azure.com/scalesetpriority",
                                    "operator": "Equal",
                                    "value": "spot",
                                    "effect": "NoSchedule",
                                },
                            ],
                            "serviceAccountName": self.name,
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                            "initContainers": [wait_for_pod("rabbitmq")],
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
                            ],
                        },
                    },
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, RoleBinding, Service, Deployment]:
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.rolebinding, self.service, self.deployment)
