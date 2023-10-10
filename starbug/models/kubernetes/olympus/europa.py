"""Defines a Europa Instance."""

from kr8s.objects import Deployment, Job, Service, ServiceAccount

from starbug.logic.secrets import get_secret_value


class Europa:
    """Defines a Europa Instance."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the Europa class."""
        self.namespace = namespace
        self.name = "europa"
        self.image = image or "binkcore.azurecr.io/europa:prod"
        self.labels = {"app": "europa"}
        self.env = {
            "ENVIRONMENT_ID": "ait",
            "SENTRY_DSN": "https://63978f8a2fc04916bb67ea5e5e2f20ef@o503751.ingest.sentry.io/5778752",
            "TEAMS_WEBHOOK": "https://hellobink.webhook.office.com/webhookb2/bf220ac8-d509-474f-a568-148982784d19@a6e2367a-92ea-4e5a-b565-723830bcc095/IncomingWebhook/097759f226dd4be69a9f8a53d69a2e4f/ff7b6241-3a2d-471f-aa0c-cfefd7ce3a8f",
            "EUROPA_DATABASE_URI": "postgres://postgres:5432/europa",
            "KEYVAULT_URI": get_secret_value("azure-keyvault", "url"),
        }
        self.serviceaccount = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "annotations": {
                "azure.workload.identity/client-id": get_secret_value("azure-identities", "europa_client_id"),
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
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "command": ["linkerd-await", "--shutdown", "--"],
                                "args": ["python", "manage.py", "migrate"],
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
                        "containers": [
                            {
                                "name": self.name,
                                "image": self.image,
                                "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                "ports": [{"containerPort": 9000}],
                            },
                        ],
                    },
                },
            },
        })

    def everything(self) -> tuple(ServiceAccount, Service, Job, Deployment):
        """Return all deployable objects as a tuple."""
        return (self.serviceaccount, self.service, self.migrator, self.deployment)
