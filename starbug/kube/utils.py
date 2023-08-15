import kubernetes
import pendulum


class JobTimeoutError(Exception):
    """Custom Exception for when Kubernetes Jobs have not completed in a respectable timeframe."""


def await_kube_job(namespace: str, labels: dict, timeout: int = 300) -> None:
    """Awaits the completion of a Kubernetes Job."""
    w = kubernetes.watch.Watch()
    start_time = pendulum.now()
    label_selector = ",".join(["=".join([k, str(v)]) for k, v in labels.items()])
    kubernetes.config.load_config()
    for event in w.stream(
        kubernetes.client.BatchV1Api().list_namespaced_job,
        namespace=namespace,
        label_selector=label_selector,
        watch=True,
    ):
        if event["object"].status.succeeded == 1:
            w.stop()
        if (pendulum.now() - start_time).seconds > timeout:
            raise JobTimeoutError


def create_kube_object(obj: dict) -> None:
    """Create a Kubernetes Object from a Dictionary."""
    kubernetes.config.load_config()
    with kubernetes.client.ApiClient() as client:
        kubernetes.utils.create_from_dict(client, obj)


def delete_kube_namespace(namespace: str) -> None:
    """Delete a Kubernetes Namespace."""
    kubernetes.config.load_config()
    kubernetes.client.CoreV1Api().delete_namespace(name=namespace)


def get_kube_job_status(namespace: str, labels: dict) -> None:
    label_selector = ",".join(["=".join([k, str(v)]) for k, v in labels.items()])
    kubernetes.config.load_config()
    response = kubernetes.client.BatchV1Api().list_namespaced_job(namespace=namespace, label_selector=label_selector)
    status = "ongoing"
    if response.items[0].status.succeeded is not None:
        status = "complete"
    elif response.items[0].status.failed is not None:
        status = "failed"
    return {"status": status}
