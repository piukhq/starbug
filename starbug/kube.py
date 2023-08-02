"""Package containing components for interacting with Kubernetes."""

import uuid

import kubernetes


class Kube:
    """Class containing Kubernetes interactions."""

    def __init__(self, test_id: str | None = None) -> None:
        """Initialise the Kube Class."""
        self.test_id = test_id or str(uuid.uuid4())
        self.test_spec = {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": f"starbug-{self.test_id}",
                "namespace": "default",
                "labels": {
                    "created-by": "starbug",
                    "test-id": self.test_id,
                },
            },
            "spec": {
                "template": {
                    "metadata": {
                        "labels": {
                            "created-by": "starbug",
                            "test-id": self.test_id,
                        },
                        "annotations": {
                            "kubectl.kubernetes.io/default-container": "app",
                            # "linkerd.io/inject": "enabled",
                        },
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "app",
                                "image": "docker.io/ubuntu:latest",
                                "command": ["bash", "-c", "sleep 60 && echo 'Yo yo yo test is dunzo'"],
                            },
                        ],
                        "restartPolicy": "Never",
                    },
                },
            },
        }
        kubernetes.config.load_config()

    def create_job(self) -> None:
        k = kubernetes.client.ApiClient()
        kubernetes.utils.create_from_dict(k, self.test_spec)

    def check_job(self) -> str:
        k = kubernetes.client.CoreV1Api()
        pod = k.list_namespaced_pod(
            namespace="default",
            label_selector=f"created-by=starbug,test-id={self.test_id}",
        )
        return pod.items[0].status.phase

    def job_logs(self) -> str:
        k = kubernetes.client.CoreV1Api()
        pod = (
            k.list_namespaced_pod(
                namespace="default",
                label_selector=f"created-by=starbug,test-id={self.test_id}",
            )
            .items[0]
            .metadata.name
        )
        return k.read_namespaced_pod_log(pod, namespace="default")
