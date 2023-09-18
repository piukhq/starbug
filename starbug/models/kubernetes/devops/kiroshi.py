"""Define a Kiroshi Instance."""
from kr8s.objects import Deployment, Job, Service, ServiceAccount


class Kiroshi:
    """Define a Kiroshi Instance."""

    def __init__(self, namespace: str) -> None:
        """.Initialize the Kiroshi class."""
        self.namespace = namespace
        self.name = "kiroshi"
        self.image = "binkcore.azurecr.io/kiroshi:prod"
        self.labels = {"app": "kiroshi"}
        self.env = [
            {
                "name": "blob_storage_account_dsn",
                "value": "DefaultEndpointsProtocol=https;AccountName=uksouthait20kg;AccountKey=KFqNoI2CrSyVsbZlysXfz52FZMY7Fj7a0aOy2UNtwVpGk94Chda0Vd86+bVH2mxkeYu/CCDbtJPo+ASt+anamQ==;EndpointSuffix=core.windows.net",
            },
            {
                "name": "database_dsn",
                "value": "postgresql://postgres@postgres:5432/postgres",
            },
        ]
        self.service_account = ServiceAccount({
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
            },
        })
        self.migrator = Job({
            "apiVersion": "v1",
            "kind": "Job",
            "metadata": {
                "name": self.name + "-migrator",
                "namespace": self.namespace,
                "labels": self.labels,
            },
            "spec": {
                "backoffLimit": 10,
                "selector": self.labels,
                "template": {
                    "metadata": {
                        "labels": self.labels,
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "app",
                        },
                    },
                    "spec": {
                        "restartPolicy": "OnFailure",
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "app",
                                "command": ["linkerd-await", "--shutdown", "--"],
                                "args": ["bash", "-c", "while ! alembic upgrade head; do sleep 10; done"],
                                "env": self.env,
                                "image": self.image,
                            },
                        ],
                    },
                },
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
                "ports": [{"port": 80, "targetPort": 6502}],
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
                "selector": {
                    "matchLabels": self.labels,
                },
                "template": {
                    "metadata": {
                        "labels": self.labels,
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "app",
                        },
                    },
                    "spec": {
                        "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                        "serviceAccountName": self.name,
                        "containers": [
                            {
                                "name": "app",
                                "image": self.image,
                                "args": ["kiroshi","server","image"],
                                "env": self.env,
                                "ports": [{"name": "http", "containerPort": 6502, "protocol": "TCP"}],
                            },
                        ],
                    },
                },
            },
        })

    def __iter__(self) -> tuple[Job, ServiceAccount, Service, Deployment]:
        """Iterate over the Kiroshi Instance."""
        yield from (self.serviceaccount, self.migrator, self.service, self.deployment)
