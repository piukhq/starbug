"""Provides a test suite for Kiroshi."""

from kr8s.objects import Job, Role, RoleBinding, ServiceAccount

from starbug.kubernetes import wait_for_pod
from starbug.kubernetes.internal.scutter import scutter_container, scutter_role, scutter_rolebinding


class TestKiroshi:
    """Provides a test suite for Kiroshi."""

    def __init__(self, namespace: str, image: str | None = None) -> None:
        """Initialize the TestKiroshi Class."""
        self.name = "test-kiroshi"
        self.namespace = namespace
        self.image = image or "binkcore.azurecr.io/kiroshi-test:latest"
        self.serviceaccount = ServiceAccount(
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                },
            },
        )
        self.scutter_role = scutter_role(namespace=self.namespace)
        self.scutter_rolebinding = scutter_rolebinding(namespace=self.namespace, service_account_name=self.name)
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
        self.test = Job(
            {
                "apiVersion": "batch/v1",
                "kind": "Job",
                "metadata": {
                    "name": self.name,
                    "namespace": self.namespace,
                    "labels": {
                        "app": self.name,
                    },
                },
                "spec": {
                    "template": {
                        "metadata": {
                            "name": self.name,
                            "labels": {
                                "app": self.name,
                            },
                            "annotations": {
                                "kubectl.kubernetes.io/default-container": "test",
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
                            "initContainers": [wait_for_pod("kiroshi")],
                            "containers": [
                                {
                                    "name": "test",
                                    "image": self.image,
                                    "imagePullPolicy": "Always",
                                    "restartPolicy": "Never",
                                    "command": ["linkerd-await", "--"],
                                    "args": [
                                        "pytest",
                                        "image_server.py",
                                        "--html",
                                        "/mnt/results/report.html",
                                        "--self-contained-html",
                                    ],
                                    "volumeMounts": [{"name": "results", "mountPath": "/mnt/results"}],
                                },
                                scutter_container(filename="report.html"),
                            ],
                            "restartPolicy": "Never",
                            "volumes": [{"name": "results", "emptyDir": {"medium": "Memory"}}],
                        },
                    },
                    "backoffLimit": 0,
                },
            },
        )

    def deploy(self) -> tuple[ServiceAccount, Role, RoleBinding, RoleBinding, Job]:
        """Deploy the Kiroshi Test Suite."""
        return (self.serviceaccount, self.scutter_role, self.scutter_rolebinding, self.rolebinding, self.test)
