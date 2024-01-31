"""Defines a Pyqa-apiv2 Instance."""

from kr8s.objects import Deployment, Job, RoleBinding, Service, ServiceAccount
# unable to import from kr8s
from starbug.kubernetes import get_secret_value, wait_for_pod
from starbug.kubernetes.custom.resources import SecretProviderClass

class Pyqa:
    "Defines a Pyqa Instance."

    def __init__(self, name, namespace, image, secret, replicas=1):
        self.namespace = namespace
        self.name = "pyqa-apiv2"
        self.image = image or "binkcore.azurecr.io/pyqa-apiv2:latest"
        self.labels = {"app": "pyqa-apiv2"}
        self.env = {
            "ALERT_ON_FAILURE": "True",
            "ALERT_ON_SUCESS": "True",
            "COMMAND": "pytest --html report.html --self-contained-html -m bink_regression_api2 --channel bink --env staging",
            "FRIENDLY_NAME": "Staging - Bank API V2.0",
            "REPORT_CONTAINER": "qareports",
            "REPORT_DIRECTORY": "qareports",
            "SCHEDULE": "0 0 * * *",
            "TEAMS_WEBHOOK": "https://hellobink.webhook.office.com/webhookb2/bf220ac8-d509-474f-a568-148982784d19@a6e2367a-92ea-4e5a-b565-723830bcc095/IncomingWebhook/0856493823a1484b9adfa37c942d2da4/48aca6b1-4d56-4a15-bc92-8aa9d97300df"
        }


        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "annotations": {
                        "azure.workload.identity/client-id": get_secret_value("azure-identities", "pyqa_client_id"),
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
                            "restartPolicy": "Never",
                            "imagePullSecrets": [{"name": "binkcore.azurecr.io"}],
                            "containers": [
                                {
                                    "name": self.name,
                                    "image": self.image,
                                    "env": [{"name": k, "value": v} for k, v in self.env.items()],
                                    "command": ["linkerd-await", "--"],
                                    "args": [
                                        "bash",
                                        "-c",
                                        "pytest --html /tmp/report.html --self-contained-html -m bink_regression_api2 --channel bink --env staging && echo $? > /tmp/status.txt || true"],
                                    "securityContext": {
                                        "runAsGroup": 0,
                                        "runAsUser": 0,
                                    },
                                },
                            ],
                        },
                    },
                },
            },
        )
