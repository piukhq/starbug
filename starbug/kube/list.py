"""Base Model for Kubernetes Lists."""

from starbug.kube.common import KubernetesModel


class List(KubernetesModel):
    """Create a Kubernetes List Object."""

    api_version: str = "v1"
    kind: str = "List"
    items: list
